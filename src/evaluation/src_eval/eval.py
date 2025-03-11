import utils
import prompts
import json
import re
import os
import numpy as np

class BaseEvaluator():
    def __init__(
        self,
        dataset_name,
        output_dir,
    ):
        self.history = []
        self.dialogue_scores = []
        
    def _get_completion(self, prompt):
        return utils.get_completion(prompt, self.history)

## Evaluate Interaction
class InteractionEvaluator(BaseEvaluator):
    def __init__(
        self,
        dataset_name,
        output_dir,
    ):
        super().__init__(
            output_dir=output_dir,
            dataset_name=dataset_name,
        )
    
    ## Format Prompt
    def _prompt_formatter(self, dialogue_history, dialogue, flag, less):
        prompt = prompts.interaction.format(dialogue_history = dialogue_history, dialogue = dialogue, less = less)

        if flag == 1:
            prompt = prompts.interaction.format(dialogue_history = dialogue_history, dialogue = dialogue, less = less)

        return prompt
    
    ## Get Score
    def _get_score(self, prompt, turns, i, dialogue_history, dialogue):
        mscore = {}
        if turns == 2:
            mscore['0'] = {
            "互动性": 0,
            "专业性": 0,
            "逻辑性": 0,
            "解释": "只有两轮"
            }
            mscore['0']['dialogue'] = ''
            mscore['0']['dialogue_history'] = dialogue_history

        # Regenerate utill completion
        score = utils.get_completion(prompt, self.history)[0]
        while len(re.findall(r'"互动性": ([0-9]|10),', score)) == 0 or len(re.findall(r'"专业性": ([0-9]|10),', score)) == 0 or len(re.findall(r'"逻辑性": ([0-9]|10),', score)) == 0:
            score = utils.get_completion(prompt, self.history)[0]
        mscore[str(i)] = {
            "互动性": int(re.findall(r'"互动性": ([0-9]|10),', score)[0]),
            "专业性": int(re.findall(r'"专业性": ([0-9]|10),', score)[0]),
            "逻辑性": int(re.findall(r'"逻辑性": ([0-9]|10),', score)[0])
        }
        mscore[str(i)]['dialogue'] = dialogue
        mscore[str(i)]['dialogue_history'] = dialogue_history
        
        return mscore
    
    ## Reformat Dialogue
    def _dialogue_reformatter(self, d):
        dialog_history = d['dialog_history']
        dialogue_history = ''
        turns = dialog_history[-1]['turn']
        less = d['less']
        scores = dict()
        
        # turn zero and turn one
        for j in [0, 1]:
            role = dialog_history[j]['role'].replace('Lawyer','律师').replace('Plaintiff', '原告')
            content = dialog_history[j]['content']
            dialogue_history += f'{role}：{content}\n'
        
        # other turns
        for i in range(2, turns, 2):
            for item in dialog_history:
                if item['turn'] == i-1:
                    role = item['role'].replace('Lawyer','律师').replace('Plaintiff', '原告')
                    content = item['content']
                    dialogue_history += f'{role}：{content}\n'
                if item['turn'] == i and item['role'] == 'Plaintiff':
                    role = item['role'].replace('Plaintiff', '原告')
                    content = item['content']
                    dialogue_history += f'{role}：{content}\n'
                if item['turn'] == i and item['role'] == 'Lawyer':
                    role = item['role'].replace('Lawyer', '律师')
                    content = item['content']
                    dialogue = f'{role}：{content}\n'
                    
            prompt = self._prompt_formatter(dialogue_history, dialogue, 0, less)
            mscore = self._get_score(prompt, turns, i, dialogue_history, dialogue)
            print(f'turn {i} done.')
            scores[str(i)] = mscore
            dialogue_history += f'{role}：{content}\n'
            
        # the last turn
        flag = 0
        if turns % 2 == 0 and i == turns-2:
            r = turns-1
            dialogue_history += dialogue
            for item in dialog_history:
                if item['turn'] == r and item['role'] == 'Plaintiff':
                    role = item['role'].replace('Plaintiff', '原告')
                    content = item['content']
                    dialogue_history += f'{role}：{content}\n'
                if item['turn'] == r and item['role'] == 'Lawyer':
                    role = item['role'].replace('Lawyer', '律师')
                    content = item['content']
                    dialogue = f'{role}：{content}\n'
            flag = 1
            prompt = self._prompt_formatter(dialogue_history, dialogue, flag, less)
            scores = self._get_score(prompt, turns, turns, dialogue_history)
            
        return scores
    
        
    
## Evaluate Goal
class GoalEvaluator(BaseEvaluator):
    def __init__(self, dataset_name, output_dir):
        super().__init__(dataset_name, output_dir)
    
    def _string_to_json(self, input_str):
        items = input_str.replace('身份', '，身份').strip('，').split('，')
        items = [item for item in items if item != '']
        result = []
        temp = []

        for item in items:
            if item.startswith('身份：'):
                if temp:
                    result.append(temp)
                    temp = []
            temp.append(item)

        if temp and temp!='':
            result.append(temp)

        results = []
        for item in result:
            data = {}
            for i in range(len(item)):
                temp = item[i]
                if '：' in temp:
                    key, value = temp.split('：')
                    data[key] = value
                else:
                    data[key] = data[key]
            results.append(data)
        return results
        
    ## Reformat Personal Info
    def _reformat_p_info(self, input_str):
        items = input_str.replace('身份', '，身份').strip('，').split('，')
        items = [item for item in items if item != '']
        result = []
        temp = []

        for item in items:
            if item.startswith('身份：'):
                if temp:
                    result.append(temp)
                    temp = []
            temp.append(item)

        if temp:
            result.append(temp)

        results = []
        for item in result:
            data = {}
            for i in range(len(item)):
                temp = item[i]
                if '：' in temp:
                    key, value = temp.split('：')
                    data[key] = value
                else:
                    data[key] = data[key]
            results.append(data)
        return results  
    
    ## get date
    def _get_date(self, string):
        if '日' in string:
            date_pattern = r'(\d{4})年(0?[1-9]|1[0-2])月(0?[1-9]|[12][0-9]|3[01])日'
            if len(re.findall(date_pattern, string)) > 0:
                date = re.findall(date_pattern, string)[0]
            elif 'xxxx年xx月xx日':
                date = ['xxxx', 'xx', 'xx']
            return f'{date[0]}年{date[1]}月{date[2]}日'
    
        else:
            return None
        
    ## split info to personal info and others
    def _split_info(self, indictment):
        keywords = ["诉讼请求", "事实和理由", "证据和证据来源，证人姓名和住所"]
        
        pattern = '|'.join(map(re.escape, keywords))
        parts = re.split(pattern, indictment)
        
        # 提取个人信息和其他信息
        p_info = parts[0].strip()  # 个人信息
        others = ' '.join(part.strip() for part in parts[1:])  # 其他信息
        
        return p_info, others
        
    ## eval personal info
    def _eval_person_info(self, d_ground_truth, p_info):
        # Plaintiff
        count1 = 0
        plaintiff = d_ground_truth['plaintiff']
        plaintiff = self._string_to_json(plaintiff)[0]
        if d_ground_truth['plaintiff_type'] == 'personal':
            keys = ['姓名', '性别', '出生日期', '民族', '地址']
            for key in keys:
                truth = plaintiff[key]
                if truth in p_info:
                    count1 += 1
            t_count1 = 5
        else:
            keys = ['公司名称', '地址', '负责人或法定代表人']
            for key in keys:
                truth = plaintiff[key]
                if truth in p_info:
                    count1+=1
            t_count1 = 3
        plaintiff_score = count1/t_count1
        
        # Defendant
        count2 = 0
        t_count2 = 0
        defendants = d_ground_truth['defendant']
        defendants = self._string_to_json(defendants)
        for defendant in defendants:
            if '负责人或法定代表人' in defendant:
                t_count2+=3
                keys = ['公司名称', '地址', '负责人或法定代表人']
                for key in keys:
                    truth = defendant[key]
                    if truth in p_info:
                        count2 += 1
            else:
                t_count2 += 5
                keys = ['姓名', '性别', '出生日期', '民族', '地址']
                for key in keys:
                    truth = defendant[key]
                    if truth in p_info:
                        count2 += 1
        defendant_score = count2/t_count2
        
        return plaintiff_score, defendant_score
    
    ## split string to three sections
    def _split_string(self,input_str):
        sections = {
            "事实和理由": "",
            "诉讼请求": "",
            "证据": ""
        }

        current_section = None

        for line in input_str.splitlines():
            line = line.strip()
            if "事实和理由" in line:
                current_section = "事实和理由"
            elif "诉讼请求" in line:
                current_section = "诉讼请求"
            elif "证据和证据来源，证人姓名和住所" in line:
                current_section = "证据"
                
                
            if current_section:
                sections[current_section] += line + "\n"
        
        # Remove trailing newlines and return results
        for key in sections:
            sections[key] = sections[key].strip()
        
        return sections
    
    ## eval F&R, claims, evidence
    def _eval_fact_claim_evidence(self, d_ground_truth, rest):
        sections = self._split_string(rest)
        claim = sections['诉讼请求'].replace('诉讼请求：', '')
        r_f = sections['事实和理由'].replace('事实和理由：', '')
        evidence = sections['证据'].replace('证据和证据来源，证人姓名和住所：', '').split('\n\n')[0]
        g_t_claim = d_ground_truth['claim']['非诉讼费用内容']+'。' + d_ground_truth['claim']['诉讼费用内容']
        g_t_evi = ''.join(d_ground_truth['evidence']['原告'])
        prompt_claim = prompts.local.format(generated=claim, ground_truth=g_t_claim)
        prompt_r_f = prompts.local.format(generated=r_f, ground_truth=d_ground_truth['case_r_f'])
        prompt_evi = prompts.local.format(generated=evidence, ground_truth=g_t_evi)
        score_claim = utils.get_completion(prompt_claim, [])[0]
        score_r_f = utils.get_completion(prompt_r_f, [])[0]
        score_evidence = utils.get_completion(prompt_evi, [])[0]
        
        return score_claim, score_r_f, score_evidence
    
    ## eval standardability and professionality
    def _eval_global(self, d_ground_truth, indictment):
        globe_stand_prompt = prompts.globe_stand.format(generated=indictment)
        globe_prof_prompt = prompts.globe_prof.format(standard=d_ground_truth['output'],generated=indictment)
        return utils.get_completion(globe_stand_prompt, [])[0], utils.get_completion(globe_prof_prompt, [])[0]
    
    
    
    ## get scores
    def _get_scores(self, d_ground_truth, d_test_sample):
        indictment = d_test_sample['dialog_history'][-1]['content']
        p_info, rest = self._split_info(indictment.replace('（无）', '：').replace('事实与理由', '事实和理由'))
        plain_count, def_count = self._eval_person_info(d_ground_truth, p_info) 
        score_claim, score_r_f, score_evidence = self._eval_fact_claim_evidence(d_ground_truth, rest) 
        score_stand, score_prof = self._eval_global(d_ground_truth, indictment)
        score_globe = {
            "模板": score_stand,
            "专业": score_prof
            }
        results= {
            'case_id': d_test_sample['case_id'],
            'score_claim': score_claim,
            "score_r_f": score_r_f,
            "score_evidence": score_evidence,
            "score_globe": score_globe,
            "indictment": indictment,
            "ground_truth_claim": d_ground_truth['claim']['非诉讼费用内容']+'。' + d_ground_truth['claim']['诉讼费用内容'],
            "ground_truth_case_r_f": d_ground_truth['case_r_f'],
            "ground_truth_evidence": ''.join(d_ground_truth['evidence']['原告']),
            "ground_truth_globe": d_ground_truth['output'],
            "plain_accuracy": plain_count,
            "def_accuracy": def_count
            }
    
        return results