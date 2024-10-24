import streamlit as st
import boto3
import json
import time
from typing import Dict, List

class BedrockPromptFlow:
    def __init__(self):
        self.session = boto3.Session(
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
            region_name=st.secrets["AWS_REGION"]
        )
        
        # Initialize Bedrock client for prompt flows
        self.bedrock = self.session.client(
            service_name='bedrock',
            region_name=st.secrets["AWS_REGION"]
        )
        
        self.prompt_flow_id = st.secrets["PROMPT_FLOW_ID"]

    def list_prompt_flows(self):
        """List all available prompt flows"""
        try:
            response = self.bedrock.list_prompt_flows()
            return response.get('promptFlowSummaries', [])
        except Exception as e:
            st.error(f"Error listing prompt flows: {str(e)}")
            return []

    def invoke_prompt_flow(self, prompt: str) -> str:
        try:
            # Prepare the input data
            input_data = {
                "input": prompt,
                "additional_params": {
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            }

            # Invoke the prompt flow
            response = self.bedrock.invoke_prompt_flow(
                promptFlowId=self.prompt_flow_id,
                input=json.dumps(input_data)
            )
            
            # Parse the response
            if 'output' in response:
                return json.loads(response['output'])
            return None
            
        except Exception as e:
            st.error(f"Error invoking prompt flow: {str(e)}")
            return None

def initialize_session_state():
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'messages' not in st.session_state:
        st.session_state.messages = []

def main():
    st.title("🤖 Bedrock Prompt Flow Assistant")
    
    initialize_session_state()
    
    try:
        prompt_flow = BedrockPromptFlow()
        
        # Debug section in sidebar
        with st.sidebar:
            st.header("Debug Information")
            
            st.subheader("Current Configuration")
            st.write(f"Region: {st.secrets['AWS_REGION']}")
            st.write(f"Prompt Flow ID: {st.secrets['PROMPT_FLOW_ID']}")
            
            st.subheader("Available Prompt Flows")
            flows = prompt_flow.list_prompt_flows()
            if flows:
                for flow in flows:
                    st.write(f"Flow Name: {flow.get('promptFlowName', 'N/A')}")
                    st.write(f"Flow ID: {flow.get('promptFlowId', 'N/A')}")
                    st.write("---")
            else:
                st.write("No prompt flows found in this account/region")
            
            if st.button("Clear Conversation"):
                st.session_state.conversation_history = []
                st.session_state.messages = []
                st.rerun()

    except Exception as e:
        st.error(f"Error initializing Bedrock client: {str(e)}")
        return

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            with st.spinner("Processing your request..."):
                response = prompt_flow.invoke_prompt_flow(prompt)
                
                if response:
                    full_response = response
                    message_placeholder.markdown(full_response)
                    
                    st.session_state.conversation_history.append({
                        "role": "user",
                        "content": prompt
                    })
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": full_response
                    })
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response
                    })

    # Additional settings in sidebar
    with st.sidebar:
        st.header("Settings")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
        max_length = st.slider("Max Length", 100, 2000, 1000)

if __name__ == "__main__":
    main()