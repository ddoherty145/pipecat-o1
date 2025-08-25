// baml_src/main.baml
// BAML configuration for customer support

class CustomerSupportRequest {
    user_message string
    context string
}

class CustomerSupportResponse {
    message string
    confidence_level float
    requires_escalation bool
    suggested_actions string[]
}

function CustomerSupport(request: CustomerSupportRequest) -> CustomerSupportResponse {
    client GPT4Mini
    prompt #"
        You are a customer support agent. 

        User Message: {{ request.user_message }}
        Context: {{ request.context }}

        Provide a helpful response and indicate:
        - Your confidence level (0.0 to 1.0)
        - Whether this requires escalation to a human
        - Any suggested follow-up actions

        Be concise, professional, and empathetic.
    "#
}

client<llm> GPT4Mini {
    provider openai
    options {
        model "gpt-4o-mini"
        api_key env.OPENAI_API_KEY
    }
}