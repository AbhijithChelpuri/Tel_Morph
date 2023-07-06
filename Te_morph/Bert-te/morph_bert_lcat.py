# -*- coding: utf-8 -*-
"""Morph_BERT_lcat.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1G-BerVVEXT4xtw6xzyzSYAiN_XfdoWp1
"""

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import os
import json
import csv
from sklearn.metrics import f1_score

# uploading the early stopping .py file
from google.colab import files
uploaded = files.upload()

from google.colab import drive
drive.mount('/content/drive')

# Specify the path to your CSV file
csv_file_path = '/content/drive/MyDrive/Te_Morph/cleaned_data.csv'

# Read the CSV file into a DataFrame
df = pd.read_csv(csv_file_path)

# Print the DataFrame
print(df.head())

!pip install torch
!pip install transformers
!pip install tensorflow

import torch
from transformers import BertTokenizer, BertForSequenceClassification
from sklearn.metrics import precision_score, recall_score, f1_score

!pip3 install wxconv

data = df["cleaned data"]

input_texts = []
labels = []
for line in data:
        line_parts = str(line).strip().split(",")
        input_text = line_parts[0].strip()
        label = line_parts[0:8]  # Assuming labels are in positions 1 to 7

        input_texts.append(input_text)
        labels.append(label)
        # print(label, len(label))

df_cleaned = pd.DataFrame(data = labels, columns=["root_word","lcat","gender","number","person","f","TAM","suffix"])

# Remove f column with inde
df_cleaned.drop(df_cleaned.columns[[5]], axis=1, inplace=True)

df_cleaned["tokens"]=df["tokens"]

df_cleaned = df_cleaned.drop([28820, 31985, 20175, 20055,9248,27799])

df_cleaned=df_cleaned.reset_index(drop=True)

gender_labels = df_cleaned["gender"].unique()
number_labels = df_cleaned["number"].unique()
person_labels = df_cleaned["person"].unique()
TAM_labels = df_cleaned["TAM"].unique()
suffix_labels = df_cleaned["suffix"].unique()

df_cleaned.head()

sentence=[]
la=[]
mosentences=[]
lcat_labels=[]
for i in range(len(df_cleaned["tokens"])):
  if(df_cleaned["tokens"][i]!="."):
    if(df_cleaned["lcat"][i]== 'avy' or df_cleaned["lcat"][i]== 'num' or df_cleaned["lcat"][i]== 'adv' or df_cleaned["lcat"][i]== 'n' or df_cleaned["lcat"][i]== 'nst' or df_cleaned["lcat"][i]== 'adj' or df_cleaned["lcat"][i]== 'unk' or df_cleaned["lcat"][i]== 'v' or df_cleaned["lcat"][i]== 'pn' or df_cleaned["lcat"][i]== 'punc'):
      sentence.append(df_cleaned["tokens"][i])
      la.append(df_cleaned["lcat"][i])
  else:
    sentence.append(df_cleaned["tokens"][i])
    la.append(df_cleaned["lcat"][i])
    mosentences.append(sentence)
    lcat_labels.append(la)
    sentence=[]
    la=[]

flattened_list = [item for sublist in lcat_labels for item in sublist]

# Find the distinct values using set
distinct_values = set(flattened_list)

# Print the distinct values
print(distinct_values)

df_cleaned["lcat"].value_counts()

print(mosentences[0])
print(lcat_labels[0])

# tag_values = list(set(lcat_labels))
flattened_list = [item for sublist in lcat_labels for item in sublist]
tag_values = list(set(flattened_list))

tag_values.append("PAD")
tag2idx = {t: i for i, t in enumerate(tag_values)}

print(tag_values)

import torch
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from transformers import BertTokenizer, BertConfig
from sklearn.model_selection import train_test_split
from transformers import RobertaModel, RobertaTokenizer, BertModel, BertTokenizer
#from bertviz import head_view

model = BertModel.from_pretrained("ltrctelugu/bert_ltrc_telugu", output_attentions=True)
tokenizer = BertTokenizer.from_pretrained("ltrctelugu/bert_ltrc_telugu")

# tokenize wala step ## wala step jaise gunships ##shipa
def tokenize_and_preserve_labels(sentence, text_labels):
    tokenized_sentence = []
    labels = []

    for word, label in zip(sentence, text_labels):

        # Tokenize the word and count # of subwords the word is broken into
        tokenized_word = tokenizer.tokenize(word)
        n_subwords = len(tokenized_word)

        # Add the tokenized word to the final tokenized word list
        tokenized_sentence.extend(tokenized_word)

        # Add the same label to the new list of labels `n_subwords` times
        labels.extend([label] * n_subwords)

    return tokenized_sentence, labels

tokenized_texts_and_labels = [
    tokenize_and_preserve_labels(sent, labs)
    for sent, labs in zip(mosentences, lcat_labels)
]

tokenized_texts = [token_label_pair[0] for token_label_pair in tokenized_texts_and_labels]
labels = [token_label_pair[1] for token_label_pair in tokenized_texts_and_labels]

max_length = max(mosentences, key=len)

print(len(max_length))

MAX_LEN = 71
bs = 128 #change to 64

!pip install tensorflow keras

from tensorflow.keras.preprocessing.sequence import pad_sequences

input_ids = pad_sequences([tokenizer.convert_tokens_to_ids(txt) for txt in tokenized_texts],
                          maxlen=MAX_LEN, dtype="long", value=0.0,
                          truncating="post", padding="post")

len(mosentences)

tags = pad_sequences([[tag2idx.get(l) for l in lab] for lab in lcat_labels],
                     maxlen=MAX_LEN, value=tag2idx["PAD"], padding="post",
                     dtype="long", truncating="post")

attention_masks = [[float(i != 0.0) for i in ii] for ii in input_ids]

from sklearn.model_selection import train_test_split

# Split into train and remaining data
tr_inputs, remaining_sentences, tr_tags, remaining_labels = train_test_split(input_ids, tags, test_size=0.2, random_state=2018)

# Split remaining data into validation and test sets
val_inputs, test_inputs, val_tags, test_tags = train_test_split(remaining_sentences, remaining_labels, test_size=0.5, random_state=2018)

# Split attention masks accordingly
tr_masks, remaining_masks, _, _ = train_test_split(attention_masks, mosentences, test_size=0.2, random_state=2018)
val_masks, test_masks, _, _ = train_test_split(remaining_masks, remaining_sentences, test_size=0.5, random_state=2018)

import transformers
from transformers import BertForTokenClassification, AdamW, RobertaForTokenClassification

transformers.__version__

tr_inputs = torch.tensor(tr_inputs)
val_inputs = torch.tensor(val_inputs)
tr_tags = torch.tensor(tr_tags)
val_tags = torch.tensor(val_tags)
tr_masks = torch.tensor(tr_masks)
val_masks = torch.tensor(val_masks)
test_inputs=torch.tensor(test_inputs)
test_tags=torch.tensor(test_tags)
test_masks = torch.tensor(test_masks)

#training time shuffling of the data and testing time we pass them sequentially
train_data = TensorDataset(tr_inputs, tr_masks, tr_tags)
train_sampler = RandomSampler(train_data)
train_dataloader = DataLoader(train_data, sampler=train_sampler, batch_size=bs)

valid_data = TensorDataset(val_inputs, val_masks, val_tags)
valid_sampler = SequentialSampler(valid_data)
valid_dataloader = DataLoader(valid_data, sampler=valid_sampler, batch_size=bs)

test_data = TensorDataset(test_inputs, test_masks, test_tags)
test_sampler = RandomSampler(test_data)
test_dataloader = DataLoader(test_data, sampler=test_sampler, batch_size=bs)



model = BertForTokenClassification.from_pretrained(
    "ltrctelugu/bert_ltrc_telugu",
    num_labels=len(tag2idx),
    output_attentions = True,
    output_hidden_states = True
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
n_gpu = torch.cuda.device_count()

model.cuda();

FULL_FINETUNING = True
if FULL_FINETUNING:
    param_optimizer = list(model.named_parameters())
    no_decay = ['bias', 'gamma', 'beta']
    optimizer_grouped_parameters = [
        {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)],
         'weight_decay_rate': 0.01},
        {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)],
         'weight_decay_rate': 0.0}
    ]
else:
    param_optimizer = list(model.classifier.named_parameters())
    optimizer_grouped_parameters = [{"params": [p for n, p in param_optimizer]}]

optimizer = AdamW(
    optimizer_grouped_parameters,
    lr=3e-5,
    eps=1e-8
)

from pytorchtools import EarlyStopping

#schduler to reduce learning rate linearly throughout the epochs
from transformers import get_linear_schedule_with_warmup

epochs = 30 # change to 20
max_grad_norm = 1.0

# Total number of training steps is number of batches * number of epochs.
total_steps = len(train_dataloader) * epochs

# Create the learning rate scheduler.
scheduler = get_linear_schedule_with_warmup(
    optimizer,
    num_warmup_steps=0,
    num_training_steps=total_steps
)

from sklearn.metrics import f1_score,precision_score,recall_score
from tqdm import tqdm, trange
from sklearn.preprocessing import MultiLabelBinarizer
def flat_accuracy(preds, labels):
    pred_flat = np.argmax(preds, axis=2).flatten()
    labels_flat = labels.flatten()
    return np.sum(pred_flat == labels_flat) / len(labels_flat)
def lists_lists(preds, labels):
    pred_tags = []
    true_tags = []
    for p, l in zip(preds, labels):
        temp = []
        for p_i, l_i in zip(p, l):
            if tag_values[l_i] != "PAD":
                temp.append(tag_values[p_i])
        pred_tags.append(temp)
    for l in labels:
        temp = []
        for l_i in l:
            if tag_values[l_i] != "PAD":
                temp.append(tag_values[l_i])
        true_tags.append(temp)
    return pred_tags, true_tags
# In[2]:

## Store the average loss after each epoch so we can plot them.
loss_values, validation_loss_values = [], []
early_stopping = EarlyStopping(patience=50, verbose=True)
for _ in trange(epochs, desc="Epoch"):
    # ========================================
    #               Training
    # ========================================
    # Perform one full pass over the training set.

    # Put the model into training mode.
    model.train()
    # Reset the total loss for this epoch.
    total_loss = 0

    # Training loop
    for step, batch in enumerate(train_dataloader):
        # add batch to gpu
        batch = tuple(t.to(device) for t in batch)
        b_input_ids, b_input_mask, b_labels = batch
        # Always clear any previously calculated gradients before performing a backward pass.
        model.zero_grad()
        # forward pass
        # This will return the loss (rather than the model output)
        # because we have provided the `labels`.
        outputs = model(b_input_ids, token_type_ids=None,
                        attention_mask=b_input_mask, labels=b_labels)
        # get the loss
        loss = outputs[0]
        # Perform a backward pass to calculate the gradients.
        loss.backward()
        # track train loss
        total_loss += loss.item()
        # Clip the norm of the gradient
        # This is to help prevent the "exploding gradients" problem.
        torch.nn.utils.clip_grad_norm_(parameters=model.parameters(), max_norm=max_grad_norm)
        # update parameters
        optimizer.step()
        # Update the learning rate.
        scheduler.step()

    # Calculate the average loss over the training data.
    avg_train_loss = total_loss / len(train_dataloader)
    print("Average train loss: {}".format(avg_train_loss))

    # Store the loss value for plotting the learning curve.
    loss_values.append(avg_train_loss)


    # ========================================
    #               Validation
    # ========================================
    # After the completion of each training epoch, measure our performance on
    # our validation set.

    # Put the model into evaluation mode
    model.eval()
    # Reset the validation loss for this epoch.
    eval_loss, eval_accuracy = 0, 0
    nb_eval_steps, nb_eval_examples = 0, 0
    predictions , true_labels = [], []
    for batch in valid_dataloader:
        batch = tuple(t.to(device) for t in batch)
        b_input_ids, b_input_mask, b_labels = batch

        # Telling the model not to compute or store gradients,
        # saving memory and speeding up validation
        with torch.no_grad():
            # Forward pass, calculate logit predictions.
            # This will return the logits rather than the loss because we have not provided labels.
            outputs = model(b_input_ids, token_type_ids=None,
                            attention_mask=b_input_mask, labels=b_labels)
        # Move logits and labels to CPU
        logits = outputs[1].detach().cpu().numpy()
        label_ids = b_labels.to('cpu').numpy()

        # Calculate the accuracy for this batch of test sentences.
        eval_loss += outputs[0].mean().item()
        eval_accuracy += flat_accuracy(logits, label_ids)
        predictions.extend([list(p) for p in np.argmax(logits, axis=2)])
        true_labels.extend(label_ids)

        nb_eval_examples += b_input_ids.size(0)
        nb_eval_steps += 1

    eval_loss = eval_loss / nb_eval_steps
    validation_loss_values.append(eval_loss)
    print("Validation loss: {}".format(eval_loss))
    print("Validation Accuracy: {}".format(eval_accuracy/nb_eval_steps))
    #pred_tags = [tag_values[p_i] for p, l in zip(predictions, true_labels)
    #                             for p_i, l_i in zip(p, l) if tag_values[l_i] != "PAD"]
    #valid_tags = [tag_values[l_i] for l in true_labels
    #                              for l_i in l if tag_values[l_i] != "PAD"]
    pred_tags,valid_tags = lists_lists(predictions, true_labels)
    mlb = MultiLabelBinarizer()
    pred_tags_binary = mlb.fit_transform(pred_tags)
    valid_tags_binary = mlb.transform(valid_tags)
    print(pred_tags)
    print(valid_tags)

# Calculate evaluation metrics
    val_f1score = f1_score(pred_tags_binary, valid_tags_binary, average='macro')
    val_precision = precision_score(pred_tags_binary, valid_tags_binary, average='macro', zero_division=1)
    val_recall = recall_score(pred_tags_binary, valid_tags_binary, average='macro')
    early_stopping(val_f1score, model)
    print("Validation F1-Score:", val_f1score)
    print("Validation Precision:", val_precision)
    print("Validation Recall:", val_recall)

    early_stopping(val_f1score, model)
    if early_stopping.early_stop:
        print("Early Stopping")
        break
    print()
model.load_state_dict(torch.load('checkpoint.pt'))
model.eval()

!pip install seqeval

model.eval()

predictions = []
true_labels = []
with torch.no_grad():
  for batch in test_dataloader:
      batch = tuple(t.to(device) for t in batch)
      b_input_ids, b_input_mask, b_labels = batch

      with torch.no_grad():
          outputs = model(b_input_ids, token_type_ids=None, attention_mask=b_input_mask)

      logits = outputs[0].detach().cpu().numpy()
      label_ids = b_labels.to('cpu').numpy()

      predictions.extend([list(p) for p in np.argmax(logits, axis=2)])
      true_labels.extend(label_ids)

# Convert predicted tags and true labels to tag names
pred_tags, test_tags = lists_lists(predictions, true_labels)

from seqeval.metrics import accuracy_score, precision_score, recall_score, f1_score

# Convert predicted tags and true labels to list of lists
pred_tags = [[tag_values[p_i] for p_i in p] for p in predictions]
true_tags = [[tag_values[l_i] for l_i in l] for l in true_labels]

# Calculate accuracy, precision, recall, and F1 scores
accuracy = accuracy_score(true_tags, pred_tags)
precision = precision_score(true_tags, pred_tags)
recall = recall_score(true_tags, pred_tags)
f1 = f1_score(true_tags, pred_tags)

# Print the scores
print("Accuracy: {}".format(accuracy))
print("precision: {}".format(precision))
print("recall: {}".format(recall))
print("f1: {}".format(f1))