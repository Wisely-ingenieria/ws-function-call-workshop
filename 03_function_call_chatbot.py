#############################################################
################## HOW TO RUN THIS EXAMPLE ##################
#############################################################

# 1. Install the required libraries by running `pip install -r requirements.txt`
# 2. Add the OpenAI API key to the `.env` file
# 3. Run the script by running `streamlit run 03_function_call_chatbot.py`

#############################################################
#############################################################

import streamlit as st
import os
import json
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt
from openai import OpenAI

load_dotenv()

GPT4O_MODEL = os.getenv("OPENAI_GPT4O_MODEL")
GPT35_MODEL = os.getenv("OPENAI_GPT35_MODEL")

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT4O_MODEL):
    try:
        response = st.session_state.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

# Funciones
sumar_scheme = {
    "type": "function",
    "function": {
        "name": "sumar",
        "description": "Sumar dos números",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "Primer número",
                },
                "b": {
                    "type": "integer",
                    "description": "Segundo número",
                },
            },
            "required": ["a", "b"],
        },
    }
}

restar_scheme = {
    "type": "function",
    "function": {
        "name": "restar",
        "description": "Restar dos números",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "Primer número",
                },
                "b": {
                    "type": "integer",
                    "description": "Segundo número",
                },
            },
            "required": ["a", "b"],
        },
    }
}

tools_scheme = [sumar_scheme, restar_scheme]

def sumar(a: int, b: int) -> int:
    return a + b

def restar(a: int, b: int) -> int:
    return a - b

def execute_tool(tool_name, parameters):
    if tool_name == "sumar":
        result = sumar(parameters["a"], parameters["b"])
    elif tool_name == "restar":
        result = restar(parameters["a"], parameters["b"])
    return result

st.title("🔧 Simple Function Call Example")

if "client" not in st.session_state:
    st.session_state.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Como te puedo ayudar?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if goal := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": goal})
    st.chat_message("user").write(goal)
    
    chat_response = chat_completion_request(st.session_state.messages, tools=tools_scheme)

    finish_reason = chat_response.choices[0].finish_reason

    if finish_reason == 'stop':
        final_answer = chat_response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": final_answer})
        st.chat_message("assistant").write(final_answer)

    elif finish_reason == 'tool_calls':
        tool_calls = chat_response.choices[0].message.tool_calls
        print(f"Tool calls: {tool_calls}")
        results = "Se ejecutaron las siguientes funciones, con sus respectivos resultados:\n\n"
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            result = execute_tool(tool_name, arguments)
            results += f"{tool_name}({arguments['a']}, {arguments['b']}) = {result}\n\n"
        
        st.session_state.messages.append({"role": "assistant", "content": results})
        st.chat_message("assistant").write(f"```\n{results}\n```")

        chat_response = chat_completion_request(st.session_state.messages)
        final_answer = chat_response.choices[0].message.content
        
        st.session_state.messages.append({"role": "assistant", "content": final_answer})
        st.chat_message("assistant").write(final_answer)