from .llm_chain_base import LLMChain

from .chat_chain import (
    Claude2ChatChain,
    Claude21ChatChain,
    ClaudeInstanceChatChain,
    Iternlm2Chat7BChatChain,
    Iternlm2Chat20BChatChain,
    Baichuan2Chat13B4BitsChatChain,
    Claude3HaikuChatChain,
    Claude3SonnetChatChain,
    # ChatGPT35ChatChain,
    # ChatGPT4ChatChain,
    # ChatGPT4oChatChain,
)

from .conversation_summary_chain import (
    Iternlm2Chat7BConversationSummaryChain,
    ClaudeInstanceConversationSummaryChain,
    Claude21ConversationSummaryChain,
    Claude3HaikuConversationSummaryChain,
    Claude3SonnetConversationSummaryChain,
    Iternlm2Chat20BConversationSummaryChain
)

from .intention_chain import (
    Claude21IntentRecognitionChain,
    Claude2IntentRecognitionChain,
    ClaudeInstanceIntentRecognitionChain,
    Claude3HaikuIntentRecognitionChain,
    Claude3SonnetIntentRecognitionChain,
    Iternlm2Chat7BIntentRecognitionChain,
    Iternlm2Chat20BIntentRecognitionChain,
    
)

from .rag_chain import (
    Claude21RagLLMChain,
    Claude2RagLLMChain,
    ClaudeInstanceRAGLLMChain,
    Claude3HaikuRAGLLMChain,
    Claude3SonnetRAGLLMChain,
    Baichuan2Chat13B4BitsKnowledgeQaChain
)


from .translate_chain import (
    Iternlm2Chat7BTranslateChain,
    Iternlm2Chat20BTranslateChain
)


from .marketing_chains import *

from .stepback_chain import (
    Claude21StepBackChain,
    ClaudeInstanceStepBackChain,
    Claude2StepBackChain,
    Claude3HaikuStepBackChain,
    Claude3SonnetStepBackChain,
    Iternlm2Chat7BStepBackChain,
    Iternlm2Chat20BStepBackChain
)


from .hyde_chain import (
    Claude21HydeChain,
    Claude2HydeChain,
    Claude3HaikuHydeChain,
    Claude3SonnetHydeChain,
    ClaudeInstanceHydeChain,
    Iternlm2Chat20BHydeChain,
    Iternlm2Chat7BHydeChain
)

from .query_rewrite_chain import (
    Claude21QueryRewriteChain,
    Claude2QueryRewriteChain,
    ClaudeInstanceQueryRewriteChain,
    Claude3HaikuQueryRewriteChain,
    Claude3SonnetQueryRewriteChain,
    Iternlm2Chat20BQueryRewriteChain,
    Iternlm2Chat7BQueryRewriteChain
)

from .tool_calling_chain_claude_xml import (
    Claude21ToolCallingChain,
    Claude3HaikuToolCallingChain,
    Claude2ToolCallingChain,
    Claude3SonnetToolCallingChain,
    ClaudeInstanceToolCallingChain
)

from .retail_chains import *