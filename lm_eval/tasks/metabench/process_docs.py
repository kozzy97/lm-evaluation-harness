import ast
import datasets
import re

def process_arc(dataset: datasets.Dataset) -> datasets.Dataset:
    def _subprocess(doc):
        long_prompt = ""
        for shot in range(1,26):
            question = doc[f"arc_question_shot_{shot}"]
            doc.pop(f"arc_question_shot_{shot}")
            answer_lab = doc[f"arc_answerKey_shot_{shot}"]
            doc.pop(f"arc_answerKey_shot_{shot}")
            answer_idx = doc[f"arc_choices_shot_{shot}"]["label"].index(answer_lab)
            answer = doc[f"arc_choices_shot_{shot}"]["text"][answer_idx]
            doc.pop(f"arc_choices_shot_{shot}")
            doc.pop(f"arc_idx_shot_{shot}")

            long_prompt = f"{long_prompt}Question: {question}\nAnswer: {answer}\n\n" #no choices are provided in the few-shot setting (per lines 602-610 of lm_eval.api.task)
        doc["twentyfive_shot_preprompt"] = long_prompt
        doc.pop("alltwentyfiveshot_longprompt")
        return doc
    return dataset.map(_subprocess)

def process_gsm8k(dataset: datasets.Dataset) -> datasets.Dataset:
    def _subprocess(doc):
        long_prompt = ""
        for shot in ["first", "second", "third", "fourth", "fifth"]:
            question = doc[f"gsm8k_{shot}shot_training_prompt"]
            doc.pop(f"gsm8k_{shot}shot_training_prompt")
            answer = doc[f"gsm8k_{shot}shot_training_answer"]
            doc.pop(f"gsm8k_{shot}shot_training_answer")
            doc.pop(f"gsm8k_{shot}shot_training_idx")

            long_prompt = f"{long_prompt}Question: {question}\nAnswer: {answer}\n\n" #no choices are provided in the few-shot setting (per lines 602-610 of lm_eval.api.task)
        doc["five_shot_preprompt"] = long_prompt
        doc.pop("allfiveshot_longprompt")
        return doc
    return dataset.map(_subprocess)

def process_hellaswag(dataset: datasets.Dataset) -> datasets.Dataset:
    def process_txt(text): #mirrored from hellaswag task
        text = text.strip()
        # NOTE: Brackets are artifacts of the WikiHow dataset portion of HellaSwag.
        text = text.replace(" [title]", ". ")
        text = re.sub("\\[.*?\\]", "", text)
        text = text.replace("  ", " ")
        return text
    
    def _preprocess(doc):
        ctx = doc["ctx_a"] + " " + doc["ctx_b"].capitalize()
        doc.pop("ctx_a")
        doc.pop("ctx_b")
        doc.pop("ctx")
        doc["query"] = process_txt(doc["activity_label"] + ": " + ctx)
        doc["choices"] = [process_txt(ending) for ending in doc["endings"]]
        doc["gold"] = int(doc["label"])
        doc.pop("activity_label")
        doc.pop("endings")

        long_prompt = ""
        for shot in range(1, 11):
            ctx = doc[f"hellaswag_ctx_a_shot_{shot}"] + " " + doc[f"hellaswag_ctx_b_shot_{shot}"].capitalize()
            doc.pop(f"hellaswag_ctx_a_shot_{shot}")
            doc.pop(f"hellaswag_ctx_b_shot_{shot}")
            doc.pop(f"hellaswag_ctx_shot_{shot}")
            question = process_txt(doc[f"hellaswag_activity_labels_shot_{shot}"] + ": " + ctx)
            ending = process_txt(doc[f"hellaswag_endings_shot_{shot}"][int(doc[f"hellaswag_label_shot_{shot}"])])
            doc.pop(f"hellaswag_activity_labels_shot_{shot}")
            doc.pop(f"hellaswag_endings_shot_{shot}")
            doc.pop(f"hellaswag_label_shot_{shot}")

            long_prompt = f"{long_prompt}{question} {ending}\n\n"

            doc.pop(f"hellaswag_ind_shot_{shot}")
            doc.pop(f"hellaswag_source_id_shot_{shot}")
            doc.pop(f"hellaswag_split_shot_{shot}")
            doc.pop(f"hellaswag_split_type_shot_{shot}")
        
        doc["ten_shot_preprompt"] = long_prompt
        doc.pop("alltenshot_longprompt")
        return doc

    return dataset.map(_preprocess)


def process_mmlu(dataset: datasets.Dataset) -> datasets.Dataset:
    def _subprocess(doc):
        choices = ["A", "B", "C", "D"]
        long_prompt = f"The following are multiple choice questions (with answers) about {' '.join(doc['subject'].split('_'))}.\n\n"
        for shot in range(1,6):
            question = doc[f"mmlu_question_shot_{shot}"].strip()
            doc.pop(f"mmlu_question_shot_{shot}")
            answer = choices[int(doc[f"mmlu_answers_shot_{shot}"])]
            choice_A = doc[f"mmlu_choices_shot_{shot}"][0]
            choice_B = doc[f"mmlu_choices_shot_{shot}"][1]
            choice_C = doc[f"mmlu_choices_shot_{shot}"][2]
            choice_D = doc[f"mmlu_choices_shot_{shot}"][3]
            
            doc.pop(f"mmlu_choices_shot_{shot}")
            doc.pop(f"mmlu_answers_shot_{shot}")
            doc.pop(f"mmlu_ind_shot_{shot}")

            long_prompt = f"{long_prompt}{question}\nA. {choice_A}\nB. {choice_B}\nC. {choice_C}\nD. {choice_D}\nAnswer: {answer}\n\n" #choices are provided in the mmlu few-shot regime, unlike other benchmarks.

        doc["five_shot_preprompt"] = long_prompt
        doc.pop("allfiveshot_longprompt")
        return doc
    return dataset.map(_subprocess)

def process_winogrande(dataset: datasets.Dataset) -> datasets.Dataset: 
    def _subprocess(doc):
        long_prompt = ""
        for shot in ["first", "second", "third", "fourth", "fifth"]:
            if doc[f"winogrande_{shot}shot_training_answer"] == "1":
                answer = doc[f"winogrande_{shot}shot_training_option1"]
            elif doc[f"winogrande_{shot}shot_training_answer"] == "2":
                answer = doc[f"winogrande_{shot}shot_training_option2"]
            else:
                raise ValueError("Answer not recognised.")
            
            question = doc[f"winogrande_{shot}shot_training_prompt"].replace("_", answer)

            doc.pop(f"winogrande_{shot}shot_training_prompt")
            doc.pop(f"winogrande_{shot}shot_training_answer")
            doc.pop(f"winogrande_{shot}shot_training_idx")
            doc.pop(f"winogrande_{shot}shot_training_option1")
            doc.pop(f"winogrande_{shot}shot_training_option2")

            long_prompt = f"{long_prompt}{question}\n\n" 
        doc["sentence"] = f"{long_prompt}{doc["sentence"]}"
        doc.pop("metabench_fiveshot_prompt")
        return doc
    return dataset.map(_subprocess)

# Mirrored from the winogrande task
def winogrande_doc_to_text(doc):
    answer_to_num = {"1": 0, "2": 1}
    return answer_to_num[doc["answer"]]


def winogrande_doc_to_target(doc):
    idx = doc["sentence"].index("_") + 1
    return doc["sentence"][idx:].strip()


def winogrande_doc_to_choice(doc):
    idx = doc["sentence"].index("_")
    options = [doc["option1"], doc["option2"]]
    return [doc["sentence"][:idx] + opt for opt in options]