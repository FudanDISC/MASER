# -*- coding: utf-8 -*-
"""
Created on Sun Sep 22 19:35:01 2024

@author: Hilbert Schweitzer
"""

import json
from openai import OpenAI
from typing import List, Tuple
from requests.exceptions import ConnectionError, Timeout, RequestException
import time
from openai_config import openai_config

api_key = openai_config["api"]
api_url = openai_config["base_url"]

def load_jsonl(file_raw: str) -> List[dict]:
    filename = file_raw
    results = []
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            json_obj = json.loads(line.strip())
            results.append(json_obj)
    
    return results


def load_files(file_raw):
    with open(file_raw, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def reorder(dictlist):
    return sorted(dictlist, key=lambda x: x['case_id'])

def save_file(output: dict, file: str):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
        
def get_completion(prompt: str, history: List[Tuple[str, str]]):
    client = OpenAI(api_key=api_key,
                    base_url=api_url)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            SYSTEM_PROMPT = """You are a helpful assistant."""
            messages = []
            messages.append({'role': 'system', "content": SYSTEM_PROMPT})
            if history != []:
                for h in history:
                    messages.append({'role':'user',"content":h[0]})
                    messages.append({'role':'assistant',"content":h[1]})
            else:
                messages.append({'role':'user',"content":prompt})
        
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="gpt-4o-2024-08-06",
                response_format={"type": "json_object"},
                max_tokens=50,
                temperature=0
                )
            
            response = chat_completion.choices[0].message.content
            history.append((prompt, response))
            time.sleep(60)
            return response, history
        
        except (ConnectionError, Timeout) as e:
            print(f"Network error occurred: {e}. Retrying {attempt + 1}/{max_retries}...")
            if attempt == max_retries - 1:
                raise  # Re-raise the last exception if all retries fail
                
        except RequestException as e:
            # Handle other types of requests exceptions
            print(f"An error occurred: {e}.")
            raise  # Re-raise the exception and exit the function
        except Exception as e:
            print(e)
            
    # Optional: Return a default message or handle the failed attempts
    return "Unable to get a response after several attempts."