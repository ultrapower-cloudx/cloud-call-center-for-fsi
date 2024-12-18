import json
import logging
import os
import re

from langchain.docstore.document import Document
from langchain.document_loaders import PDFMinerPDFasHTMLLoader

from .cleaning import remove_duplicate_sections
from .splitter_utils import MarkdownHeaderTextSplitter

logger = logging.getLogger()
logger.setLevel(logging.INFO)

metadata_template = {
    "content_type": "paragraph",
    "heading_hierarchy": {},
    "figure_list": [],
    "chunk_id": "$$",
    "file_path": "",
    "keywords": [],
    "summary": "",
}


def detect_language(input):
    """
    This function detects the language of the input text. It checks if the input is a list,
    and if so, it joins the list into a single string. Then it uses a regular expression to
    search for Chinese characters in the input. If it finds any, it returns 'ch' for Chinese.
    If it doesn't find any Chinese characters, it assumes the language is English and returns 'en'.
    """
    if isinstance(input, list):
        input = " ".join(input)
    if re.search("[\u4e00-\u9fff]", input):
        return "ch"
    else:
        return "en"


def invoke_etl_model(
    smr_client,
    etl_model_endpoint,
    bucket,
    key,
    res_bucket,
    portal_bucket_name: str,
    mode="ppstructure",
    lang="ch",
):
    response_model = smr_client.invoke_endpoint(
        EndpointName=etl_model_endpoint,
        Body=json.dumps(
            {
                "s3_bucket": bucket,
                "object_key": key,
                "destination_bucket": res_bucket,
                "portal_bucket": portal_bucket_name,
                "mode": mode,
                "lang": lang,
            }
        ),
        ContentType="application/json",
    )

    json_str = response_model["Body"].read().decode("utf8")
    json_obj = json.loads(json_str)
    markdown_prefix = json_obj["destination_prefix"]

    return markdown_prefix


def load_content_from_s3(s3, bucket, key):
    """
    This function loads the content of a file from S3 and returns it as a string.
    """
    logger.info(f"Loading content from s3://{bucket}/{key}")
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8")


def process_pdf(s3, pdf: bytes, **kwargs):
    """
    Process a given PDF file and extracts structured information from it.

    This function reads a PDF file, converts it to HTML using PDFMiner, then extracts
    and structures the information into a list of dictionaries containing headings and content.

    Parameters:
    s3 (boto3.client): The S3 client to use for downloading the PDF file.
    pdf (bytes): The PDF file to process.
    **kwargs: Arbitrary keyword arguments. The function expects 'bucket' and 'key' among the kwargs
              to specify the S3 bucket and key where the PDF file is located.

    Returns:
    list[Document]: A list of Document objects, each representing a semantically grouped section of the PDF file. Each Document object contains a metadata defined in metadata_template, and page_content string with the text content of that section.
    """
    bucket = kwargs["bucket"]
    key = kwargs["key"]
    etl_model_endpoint = kwargs.get("etl_model_endpoint", None)
    smr_client = kwargs.get("smr_client", None)
    res_bucket = kwargs.get("res_bucket", None)
    portal_bucket_name = kwargs.get("portal_bucket_name", None)
    need_split = kwargs.get("need_split", None)
    logger.info("Input arguments: {}".format(kwargs))
    # extract the file into tmp folder
    local_path = "/tmp/{}".format(os.path.basename(key))
    s3.download_file(Bucket=bucket, Key=key, Filename=local_path)
    # TODO, will be deprecated and replaced by nougat class in loader_utils
    loader = PDFMinerPDFasHTMLLoader(local_path)
    # entire PDF is loaded as a single Document
    file_content = loader.load()[0].page_content

    detected_lang = detect_language(file_content[:100000])
    logger.info(f"Detected language: {detected_lang}")

    if not etl_model_endpoint or not smr_client or not res_bucket:
        logger.error(
            "Cannot find ETL model endpoint, SMR client or result bucket, please check the arguments."
        )
    else:
        if detected_lang == "ch":
            logger.info("Detected language is Chinese, using default PDF loader...")
            markdown_prefix = invoke_etl_model(
                smr_client,
                etl_model_endpoint,
                bucket,
                key,
                res_bucket,
                portal_bucket_name,
                mode="ppstructure",
                lang="ch",
            )
            logger.info(f"Markdown file path: s3://{res_bucket}/{markdown_prefix}")
            content = load_content_from_s3(s3, res_bucket, markdown_prefix)
        else:
            logger.info("Detected language is English, using ETL model endpoint...")
            markdown_prefix = invoke_etl_model(
                smr_client,
                etl_model_endpoint,
                bucket,
                key,
                res_bucket,
                portal_bucket_name,
                mode="ppstructure",
                lang="en",
            )
            logger.info(f"Markdown file path: s3://{res_bucket}/{markdown_prefix}")
            content = load_content_from_s3(s3, res_bucket, markdown_prefix)

        # remove duplicate sections
        content = remove_duplicate_sections(content)
        metadata = {"file_path": f"s3://{bucket}/{key}", "file_type": "pdf"}
        # need_split is type of boolean, judge if we need to split the content
        if not need_split:
            return [Document(page_content=content, metadata=metadata)]

        markdown_splitter = MarkdownHeaderTextSplitter(res_bucket)
        doc_list = markdown_splitter.split_text(
            Document(page_content=content, metadata=metadata)
        )

    return doc_list
