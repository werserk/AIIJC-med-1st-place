import torch
import os
from utils import get_scheduler, get_model, get_criterion, get_optimizer, get_metric
from data_functions import get_loaders
from utils import OneHotEncoder
import wandb
from tqdm import tqdm
import time


# helping function to normal visualisation in Colaboratory
def foo_():
    time.sleep(0.3)


def train_epoch(model, train_dl, encoder, criterion, metric, optimizer, scheduler, device):
    model.train()
    loss_sum = 0
    score_sum = 0
    with tqdm(total=len(train_dl), position=0, leave=True) as pbar:
        for X, y in tqdm(train_dl, position=0, leave=True):
            pbar.update()
            X = X.to(device)
            if len(torch.unique(X)) == 1:
                continue
            if encoder is not None:
                y = encoder(y)
            y = y.squeeze(4)
            y = y.to(device)

            optimizer.zero_grad()
            output = model(X)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()
            scheduler.step()

            loss = loss.item()
            score = metric(output, y).mean().item()
            loss_sum += loss
            score_sum += score
    return loss_sum / len(train_dl), score_sum / len(train_dl)


def eval_epoch(model, val_dl, encoder, criterion, metric, device):
    model.eval()
    loss_sum = 0
    score_sum = 0
    with tqdm(total=len(val_dl), position=0, leave=True) as pbar:
        for X, y in tqdm(val_dl, position=0, leave=True):
            pbar.update()
            X = X.to(device)
            if len(torch.unique(X)) == 1:
                continue
            if encoder is not None:
                y = encoder(y)
            y = y.squeeze()
            y = y.to(device)

            with torch.no_grad():
                output = model(X)
                loss = criterion(output, y).item()
                score = metric(output, y).mean().item()
                loss_sum += loss
                score_sum += score
    return loss_sum / len(val_dl), score_sum / len(val_dl)


def run(cfg, model_name, use_wandb=True, max_early_stopping=2):
    torch.cuda.empty_cache()

    # <<<<< SETUP >>>>>
    train_loader, val_loader = get_loaders(cfg)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    model = get_model(cfg)(cfg=cfg).to(device)
    optimizer = get_optimizer(cfg)(model.parameters(), **cfg.optimizer_params)
    scheduler = get_scheduler(cfg)(optimizer, **cfg.scheduler_params)
    metric = get_metric(cfg)(**cfg.metric_params)
    criterion = get_criterion(cfg)(**cfg.criterion_params)
    encoder = OneHotEncoder(cfg)

    # wandb is watching
    if use_wandb:
        wandb.init(project='Covid19_CT_segmentation_' + str(cfg.dataset_name), entity='aiijcteamname', config=cfg,
                   name=model_name)
        wandb.watch(model, log_freq=100)

    best_val_loss = 999
    last_train_loss = 0
    last_val_loss = 999
    early_stopping_flag = 0
    best_state_dict = model.state_dict()
    for epoch in range(1, cfg.epochs + 1):
        print(f'Epoch #{epoch}')

        # <<<<< TRAIN >>>>>
        train_loss, train_score = train_epoch(model, train_loader, encoder,
                                              criterion, metric,
                                              optimizer, scheduler, device)
        print('      Score    |    Loss')
        print(f'Train: {train_score:.6f} | {train_loss:.6f}')

        # <<<<< EVAL >>>>>
        val_loss, val_score = eval_epoch(model, val_loader, encoder,
                                         criterion, metric, device)
        print(f'Val: {val_score:.6f} | {val_loss:.6f}', end='\n\n')
        metrics = {'train_score': train_score,
                   'train_loss': train_loss,
                   'val_score': val_score,
                   'val_loss': val_loss,
                   'lr': scheduler.get_last_lr()[-1]}

        if use_wandb:  # log metrics to wandb
            wandb.log(metrics)

        # saving best weights
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state_dict = model.state_dict()
            torch.save(best_state_dict, os.path.join('checkpoints', model_name + '.pth'))

        # weapon counter over-fitting
        if train_loss < last_train_loss and val_loss > last_val_loss:
            early_stopping_flag += 1
        if early_stopping_flag == max_early_stopping:
            print('<<< EarlyStopping >>>')
            break

        last_train_loss = train_loss
        last_val_loss = val_loss

    # loading best weights
    model.load_state_dict(best_state_dict)

    if use_wandb:
        wandb.finish()
    return model
