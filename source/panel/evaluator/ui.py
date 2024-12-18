import json
import os
import time
from typing import List

import altair as alt
import pandas as pd
import streamlit as st
from benchmark import WorkflowExecutor
from dotenv import load_dotenv
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.evaluation.qa import QAEvalChain
from langchain.llms import Anthropic
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.vectorstores import OpenSearchVectorSearch
from prompts import (
    GRADE_ANSWER_PROMPT,
    GRADE_ANSWER_PROMPT_BIAS_CHECK,
    GRADE_ANSWER_PROMPT_FAST,
    GRADE_ANSWER_PROMPT_OPENAI,
    GRADE_DOCS_PROMPT,
    QA_CHAIN_PROMPT_LEX,
    QA_CHAIN_PROMPT_TRAVEL,
)

load_dotenv(dotenv_path=".env")

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

oai_api_key = os.getenv("OPENAI_API_KEY")


# Keep dataframe in memory to accumulate experimental results
if "existing_df" not in st.session_state:
    summary = pd.DataFrame(
        columns=[
            "model",
            "retriever",
            "embedding",
            "num_neighbors",
            "Latency",
            "Retrieval score",
            "Answer score",
        ]
    )
    st.session_state.existing_df = summary
else:
    summary = st.session_state.existing_df


@st.cache_resource
def make_llm(model_version: str):
    """
    Make LLM from model version
    @param model_version: model_version
    @return: LLN
    """
    if (model_version == "gpt-3.5-turbo") or (model_version == "gpt-4"):
        chosen_model = ChatOpenAI(model_name=model_version, temperature=0)
    elif model_version == "anthropic":
        chosen_model = Anthropic(temperature=0)
    else:
        st.warning("`Model version not recognized. Using gpt-3.5-turbo`", icon="⚠️")
        chosen_model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    return chosen_model


@st.cache_resource
def make_retriever(retriever_type, embedding_type):
    """
    Make document retriever
    @param retriever_type: retriever type
    @param embedding_type: embedding type
    @param num_neighbors: number of neighbors for retrieval

    """
    # TODO:
    pass


def make_chain(llm):
    """
    Make retrieval chain
    @param retriever: retriever
    @param retriever_type: retriever type
    @return: QA chain
    """

    qa_chain = load_qa_chain(llm, chain_type="stuff", prompt=QA_CHAIN_PROMPT_LEX)

    return qa_chain


def grade_model_answer(
    predicted_dataset: List, predictions: List, grade_answer_prompt: str
) -> List:
    """
    Grades the distilled answer based on ground truth and model predictions.
    @param predicted_dataset: A list of dictionaries containing ground truth questions and answers.
    @param predictions: A list of dictionaries containing model predictions for the questions.
    @param grade_answer_prompt: The prompt level for the grading. Either "Fast" or "Full".
    @return: A list of scores for the distilled answers.
    """
    # Grade the distilled answer
    st.info("`Grading model answer ...`")
    # Set the grading prompt based on the grade_answer_prompt parameter
    if grade_answer_prompt == "Fast":
        prompt = GRADE_ANSWER_PROMPT_FAST
    elif grade_answer_prompt == "Descriptive w/ bias check":
        prompt = GRADE_ANSWER_PROMPT_BIAS_CHECK
    elif grade_answer_prompt == "OpenAI grading prompt":
        prompt = GRADE_ANSWER_PROMPT_OPENAI
    else:
        prompt = GRADE_ANSWER_PROMPT

    # Create an evaluation chain
    eval_chain = QAEvalChain.from_llm(
        llm=ChatOpenAI(model_name="gpt-4", temperature=0), prompt=prompt
    )

    # Evaluate the predictions and ground truth using the evaluation chain
    graded_outputs = eval_chain.evaluate(
        predicted_dataset, predictions, question_key="question", prediction_key="result"
    )

    return graded_outputs


def grade_model_retrieval(gt_dataset: List, predictions: List, grade_docs_prompt: str):
    """
    Grades the relevance of retrieved documents based on ground truth and model predictions.
    @param gt_dataset: list of dictionaries containing ground truth questions and answers.
    @param predictions: list of dictionaries containing model predictions for the questions
    @param grade_docs_prompt: prompt level for the grading. Either "Fast" or "Full"
    @return: list of scores for the retrieved documents.
    """
    # Grade the docs retrieval
    st.info("`Grading relevance of retrieved docs ...`")

    # Set the grading prompt based on the grade_docs_prompt parameter
    prompt = GRADE_DOCS_PROMPT

    # Create an evaluation chain
    eval_chain = QAEvalChain.from_llm(
        llm=ChatOpenAI(model_name="gpt-4", temperature=0), prompt=prompt
    )

    # Evaluate the predictions and ground truth using the evaluation chain
    graded_outputs = eval_chain.evaluate(
        gt_dataset, predictions, question_key="question", prediction_key="result"
    )
    return graded_outputs


def run_evaluation(
    chain, retriever, eval_set, grade_prompt, retriever_type, num_neighbors
):
    """

    Runs evaluation on a model's performance on a given evaluation dataset.
    @param chain: Model chain used for answering questions
    @param retriever:  Document retriever used for retrieving relevant documents
    @param eval_set: List of dictionaries containing questions and corresponding ground truth answers
    @param grade_prompt: String prompt used for grading model's performance
    @param retriever_type: String specifying the type of retriever used
    @param num_neighbors: Number of neighbors to retrieve using the retriever
    @return: A tuple of four items:
    - answers_grade: A dictionary containing scores for the model's answers.
    - retrieval_grade: A dictionary containing scores for the model's document retrieval.
    - latencies_list: A list of latencies in seconds for each question answered.
    - predictions_list: A list of dictionaries containing the model's predicted answers and relevant documents for each question.
    """
    st.info("`Running evaluation ...`")
    predictions_list = []
    retrieved_docs = []
    gt_dataset = []
    latencies_list = []

    for data in eval_set:

        # Get answer and log latency
        start_time = time.time()

        # Get docs
        if retriever_type == "Faiss retriever":
            docs = retriever.similarity_search(
                query=data["question"], k=num_neighbors, filter=metadata_filter
            )
        elif retriever_type == "CSDC retriever":
            docs = retriever.similarity_search(
                query=data["question"], k=num_neighbors, filter=metadata_filter
            )
        else:
            docs = retriever.similarity_search(query=data["question"], k=num_neighbors)
        logger.info("--DOCS--")
        if not docs:
            docs = [
                Document(
                    page_content="I was unable to recover any information about the question!"
                )
            ]
        logger.info(docs)

        # Get answer
        answer = chain.run(input_documents=docs, question=data["question"])
        predictions_list.append(
            {"question": data["question"], "answer": data["answer"], "result": answer}
        )
        gt_dataset.append(data)
        end_time = time.time()
        elapsed_time = end_time - start_time
        latencies_list.append(elapsed_time)

        # Get doc text
        retrieved_doc_text = ""
        for i, doc in enumerate(docs):
            retrieved_doc_text += "Doc %s: " % str(i + 1) + doc.page_content + " "
        retrieved = {
            "question": data["question"],
            "answer": data["answer"],
            "result": retrieved_doc_text,
        }
        retrieved_docs.append(retrieved)

    # Grade docs and answer
    answers_grade = grade_model_answer(gt_dataset, predictions_list, grade_prompt)
    retrieval_grade = grade_model_retrieval(gt_dataset, retrieved_docs, grade_prompt)
    return answers_grade, retrieval_grade, latencies_list, predictions_list


# Auth
st.sidebar.image("https://d0.awsstatic.com/logos/powered-by-aws.png", width=200)

with st.sidebar.form("user_input"):

    loader_type = st.radio(
        "`Choose loader`",
        (
            "unstructured loader",
            "Nougat loader",
            "CSDC loader",
        ),
        index=0,
    )

    splitter_type = st.radio(
        "`Choose splitter`",
        (
            "recursive splitter",
            "CSDC markdown header splitter",
        ),
        index=0,
    )

    embedding_type = st.radio(
        "`Choose embedding`",
        (
            "HuggingFace",
            "OpenAI",
            "CSDC",
        ),
        index=1,
    )

    retriever_type = st.radio(
        "`Choose retriever`",
        (
            "Faiss retriever",
            "CSDC retriever",
        ),
        index=0,
    )

    evaluator_type = st.radio(
        "`Choose evaluator`",
        (
            "LangChain evaluator",
            "CSDC evaluator",
        ),
        index=0,
    )

    num_neighbors = st.select_slider(
        "`Choose # chunks to retrieve`", options=[3, 4, 5, 6, 7, 8]
    )

    model = st.radio(
        "`Choose model`",
        (
            "gpt-3.5-turbo",
            "gpt-4",
            "anthropic",
            "csdc",
        ),
        index=0,
    )

    grade_prompt = st.radio(
        "`Grading style prompt`",
        ("Fast", "Descriptive", "Descriptive w/ bias check", "OpenAI grading prompt"),
        index=3,
    )

    submitted = st.form_submit_button("Submit evaluation")

# App
st.header("`AOS auto-evaluator`")
st.info(
    "`Evaluation tool for question-answering using an existing vectorDB (Amazon Open Search) and an eval set. "
    " Such tool will generate & grade an answer to each eval set question with the user-specific retrieval setting, such as metadata filtering or self-querying retrieval."
    " Experiments with different configurations are logged. For an example eval set, see eval_sets/lex-pod-eval.json.`"
)

with st.form(key="file_inputs"):

    uploaded_eval_set = st.file_uploader(
        "`Please upload eval set (.json):` ", type=["json"], accept_multiple_files=False
    )

    submitted = st.form_submit_button("Submit files")

# Build an index from the supplied docs
if uploaded_eval_set:

    if embeddings == "OpenAI":
        embedding = OpenAIEmbeddings()
    elif embeddings == "HuggingFace":
        embedding = HuggingFaceEmbeddings()

    # Eval set
    eval_set = json.loads(uploaded_eval_set.read())

    # Make LLM
    llm = make_llm(model)

    # Make retriever
    retriever = make_retriever(retriever_type, embeddings)

    # Make chain
    qa_chain = make_chain(llm)

    # Grade model
    graded_answers, graded_retrieval, latency, predictions = run_evaluation(
        qa_chain, retriever, eval_set, grade_prompt, retriever_type, num_neighbors
    )

    # Assemble outputs
    d = pd.DataFrame(predictions)
    d["answer score"] = [g["text"] for g in graded_answers]
    d["docs score"] = [g["text"] for g in graded_retrieval]
    d["latency"] = latency

    # Summary statistics
    mean_latency = d["latency"].mean()
    correct_answer_count = len(
        [text for text in d["answer score"] if "Incorrect" not in text]
    )
    correct_docs_count = len(
        [text for text in d["docs score"] if "Incorrect" not in text]
    )
    percentage_answer = (correct_answer_count / len(graded_answers)) * 100
    percentage_docs = (correct_docs_count / len(graded_retrieval)) * 100

    st.subheader("`Run Results`")
    st.info(
        "`I will grade the chain based on: 1/ the relevance of the retrieved documents relative to the question and 2/ "
        "the summarized answer relative to the ground truth answer. You can see (and change) to prompts used for "
        "grading in text_utils`"
    )
    st.dataframe(data=d, use_container_width=True)

    # Accumulate results
    st.subheader("`Aggregate Results`")
    st.info(
        "`Retrieval and answer scores are percentage of retrieved documents deemed relevant by the LLM grader ("
        "relative to the question) and percentage of summarized answers deemed relevant (relative to ground truth "
        "answer), respectively. The size of point corresponds to the latency (in seconds) of retrieval + answer "
        "summarization (larger circle = slower).`"
    )
    new_row = pd.DataFrame(
        {
            "model": [model],
            "retriever": [retriever_type],
            "embedding": [embeddings],
            "num_neighbors": [num_neighbors],
            "Latency": [mean_latency],
            "Retrieval score": [percentage_docs],
            "Answer score": [percentage_answer],
        }
    )
    summary = pd.concat([summary, new_row], ignore_index=True)
    st.dataframe(data=summary, use_container_width=True)
    st.session_state.existing_df = summary

    # Dataframe for visualization
    show = summary.reset_index().copy()
    show.columns = [
        "expt number",
        "model",
        "retriever",
        "embedding",
        "num_neighbors",
        "Latency",
        "Retrieval score",
        "Answer score",
    ]
    show["expt number"] = show["expt number"].apply(lambda x: "Expt #: " + str(x + 1))
    c = (
        alt.Chart(show)
        .mark_circle()
        .encode(
            x="Retrieval score",
            y="Answer score",
            size=alt.Size("Latency"),
            color="expt number",
            tooltip=["expt number", "Retrieval score", "Latency", "Answer score"],
        )
    )
    st.altair_chart(c, use_container_width=True, theme="streamlit")

else:
    st.warning("Please specify a AOS index and add an eval set.", icon="⚠️")
