import argparse
import re
import os
import numpy as np
import eval
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import utils

## summarize
def _final_score(results):
    t_score_claim = []
    t_score_r_f = []
    t_score_evidence = []
    t_score_stand = []
    t_score_prof = []
    t_score_plain = []
    t_score_def = []
    for d in results:
        t_score_claim.append(int(re.findall(r'([0-9]|10),', d['score_claim'])[0]))
        t_score_r_f.append(int(re.findall(r'([0-9]|10),', d['score_r_f'])[0]))
        t_score_evidence.append(int(re.findall(r'([0-9]|10),', d['score_evidence'])[0]))
        t_score_stand.append(int(re.findall(r'"规范性": ([0-9]|10),', d['score_globe']['模板'])[0]))
        t_score_prof.append(int(re.findall(r'"专业性": ([0-9]|10),', d['score_globe']['专业'])[0]))
        t_score_plain.append(d['plain_accuracy'])
        t_score_def.append(d['def_accuracy'])
        
    final_scores = {
        'Fact_and_Reason': np.mean(t_score_r_f),
        'Claim': np.mean(t_score_claim),
        'Evidence': np.mean(t_score_evidence),
        'Format': np.mean(t_score_stand),
        'Professionality': np.mean(t_score_prof),
        'ave_format_prof': np.mean(t_score_claim + t_score_prof),
        'plaintiff_accuracy': np.mean(t_score_plain),
        'defendant_accuracy': np.mean(t_score_def)
        }
    return final_scores

if __name__ == '__main__':
    ## Passing Hyperparameters
    parser = argparse.ArgumentParser(description="Hyperparameters")
    parser.add_argument(
        "--input_dir",
        help="The dir in which data are to be evaluated.",
        default="data"
    )
    parser.add_argument(
        "--output_dir",
        help = "The dir in which results are stored.",
        default="output"
    )
    parser.add_argument(
        "--tasks",
        required=True,
        help = "Tasks",
        choices = ["Interaction", "Goal"]
    )
    
    args = parser.parse_args()
    
    ## Managing Dirs
    dirname = os.path.dirname(__file__)
    basedir = os.path.join(dirname, '..')
    openai_config = os.path.join(basedir, 'openai_config.py')
    
    
    for file_name in os.listdir(args.input_dir):
        filepath = os.path.join(args.input_dir, file_name)
        
        
        data = utils.load_jsonl(filepath)
        ground_truth = utils.load_files("evaluate_data\evaluate_data.json")
        
        ## Evaluate Interaction
        dialogue_scores = {}
        if args.tasks == "Interaction":
            output_dir = os.path.join(args.output_dir, 'Interaction', file_name.replace('.jsonl', ''))
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_dir = os.path.join(output_dir, file_name.replace('.jsonl', '.json'))
            for i in range(len(data)):
                case_id = data[i]['case_id']
                data[i]['less'] = ground_truth[case_id-1]['less']

            
            InteractionEvaluator = eval.InteractionEvaluator(dataset_name=file_name.replace('.jsonl',''), output_dir=output_dir)
            
            futures=[]
            with ThreadPoolExecutor(max_workers=10) as executor:
                for idx, d in tqdm(enumerate(data[:1])):  
                    future = executor.submit(InteractionEvaluator._dialogue_reformatter, d)
                    dialogue_scores[d['case_id']] = future.result()
                    print(idx)
                    futures.append(future)
                    utils.save_file(dialogue_scores, output_dir)
    
    
        ## Evaluate Goal
        goal_scores = []
        if args.tasks == 'Goal':
            output_dir = os.path.join(args.output_dir, 'Goal', file_name.replace('.jsonl', ''))
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_dir = os.path.join(output_dir, file_name.replace('.jsonl', '.json'))
            GoalEvaluator = eval.GoalEvaluator(dataset_name=file_name.replace('.jsonl',''), output_dir=output_dir)
            
            futures=[]
            with ThreadPoolExecutor(max_workers=10) as executor:
                for idx, d in tqdm(enumerate(data)):  
                    case_id = d['case_id']
                    for item in ground_truth:
                        if item['id'] == case_id:
                            break
                    future = executor.submit(GoalEvaluator._get_scores, item, d)
                    scores = future.result()
                    goal_scores.append(scores)
                    print(idx)
                    futures.append(future)
                    utils.save_file(_final_score(goal_scores), output_dir)
                    print(f'{case_id} done.')