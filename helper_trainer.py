'''
Created on 2023年7月10日

@author: lenovo
'''

import glob
import os
import time

from cached_property import cached_property
import cv2
import pandas
from torch import nn
import torch
from torch.utils.data import DataLoader
from torch.utils.data.dataset import Dataset, random_split
from torchvision import transforms
from torchvision.io import read_image
from torchvision.transforms import ToTensor, Lambda

from helper_cmd import CmdProgress
import pandas as pd


# from mj.tool_pai import ETYPES
learning_rate = 1e-3
batch_size = 64
epochs = 30
num_class = 11#len(ETYPES)


p = transforms.Compose([transforms.Resize((28,28))])

device = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)

resize = transforms.Resize((28,28),antialias=True)

def all_element_files():
    return glob.glob(os.path.join(r'F:\workspace\mj_worker\ut\elements', '*.png'))


def resize_all():
    for i, fpath in enumerate(all_element_files()):
        print(i, fpath)
        img = read_image(fpath)
        img = resize(img)
        cv2.imwrite(os.path.join('f:/temp/28_28', os.path.basename(fpath)), img[0].numpy())

def get_train_test(full_dataset):
    train_size = int(0.8 * len(full_dataset))
    test_size = len(full_dataset) - train_size
    train_dataset, test_dataset = random_split(full_dataset, [train_size, test_size])
    return train_dataset, test_dataset


class FileBaseImageDataset(Dataset):
    def __init__(self, annotations_file=r'F:\workspace\mj_worker\ut\train.csv'):
        self.img_labels = pd.read_csv(annotations_file)

    def __len__(self):
        return len(self.img_labels)
    
    # def transform(self, x):
    #     return x.type(torch.float)
    @property
    def NC(self):
        return num_class
    
    @property
    def img_dir(self):
        return r'F:\Temp\28_28'
    
    
    def target_transform(self, y):
        return torch.zeros(self.NC, dtype=torch.float).scatter_(0, torch.tensor(y), value=1)

    def __getitem__(self, idx):
        img_path = os.path.join(self.img_dir, self.img_labels.iloc[idx, 0])
        image = read_image(img_path)
        label = self.img_labels.iloc[idx, 1]
        image = self.transform(image)
        label = self.target_transform(label)
        return image, label

# class DirectPaiImageDataset(FileBaseImageDataset):
#     img_dir = r'F:\workspace\mj_worker\ut\elements'
    
    # @classmethod
    def transform(self, x):
        return resize(x).type(torch.float)

class DbImageDataset(FileBaseImageDataset):
    def __init__(self, cls_model):
        self.cls_model = cls_model
        self.records = list(cls_model.get_training_records())

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        o = self.records[idx]
        image = o.tensor_transformed
        label = self.target_transform(o.label)
        return image, label

    @property
    def NC(self):
        return len(self.cls_model.TYPE_DN)

def get_info(a):
    a = pandas.Series(map(lambda x:x[1], a))
    return a.describe()

class DbImageDatasetCommon(FileBaseImageDataset):
    def __init__(self, cls_model, type_id, label_list):
        self.cls_model = cls_model
        self.label_list = label_list
        # self.records = list(cls_model.get_training_records(type_id))

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        o = self.records[idx]
        image = o.tensor_transformed
        label = self.target_transform(o.label_id)
        return image, label

    @cached_property
    def records(self):
        print('loading dataset...')
        return list(self.cls_model.get_training_records())
    
    @property
    def NC(self):
        return len(self.label_list)

class DbImageDatasetCommonTraining(DbImageDatasetCommon):
    def __init__(self, cls_model, label_list):
        self.cls_model = cls_model
        self.label_list = label_list
    
    @cached_property
    def records(self):
        print('loading training dataset...')
        return list(self.cls_model.get_training_records())

class DbImageDatasetCommonTesting(DbImageDatasetCommonTraining):
    @cached_property
    def records(self):
        print('loading testing dataset...')
        return list(self.cls_model.get_testing_records())



class BaseNet(object):
    def train_loop(self):
        size = len(self.train_loader.dataset)
        self.train()
        for batch, (X, y) in enumerate(self.train_loader):
            pred = self(X)
            loss = self.loss_fn(pred, y)

            loss.backward()
            self.optimizer.step()
            self.optimizer.zero_grad()

            if batch % 100 == 0:
                loss, current = loss.item(), (batch + 1) * len(X)
                print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")

    def test_loop(self):
        self.eval()
        size = len(self.test_loader.dataset)
        num_batches = len(self.test_loader)
        test_loss, correct = 0, 0

        with torch.no_grad():
            for X, y in self.test_loader:
                pred = self(X)
                test_loss += self.loss_fn(pred, y).item()
                correct += (pred.argmax(1) == y.argmax(1)).type(torch.float).sum().item()

        test_loss /= num_batches
        correct /= size
        print(f"Test Error: \n Accuracy: {(100 * correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")
        return correct, test_loss


    # def load_model(self, pth_fpath):
    #     self.load_state_dict(torch.load(pth_fpath))
    #     self.eval()

    def load_model(self,pth_fpath=None):
        pth_fpath = pth_fpath if pth_fpath is not None else self.fpath_pth
        self.load_state_dict(torch.load(pth_fpath))
        self.eval()
        return self


    def get_label_name(self, label_id):
        # print(self.label_dict)
        return self.label_dict[label_id]


    def update_train_result(self, pth_fpath):
        # self.load_model(pth_fpath)
        X, ids = self.cls_model.get_X_all(type_id=self.type_id)
        pred = self.load_model()(X)
        # l = pred.argmax(1)
        # probs = torch.sigmoid(pred)
        probs = torch.softmax(pred, dim=1)
        # p, _ = probs.max(axis=1)
        p, l = probs.max(axis=1)
        cp = CmdProgress(len(ids))
        objs = []
        for i in range(len(l)):
            o = self.cls_model.objects.get(id=ids[i])
            o.pred_label_id = int(l[i])
            o.pred_label_name = self.get_label_name(int(l[i]))
            o.prob = float(p[i])
            objs.append(o)
            cp.update()
        self.cls_model.objects.bulk_update(objs, ('pred_label_id', 'pred_label_name', 'prob'))

    def predict(self, pth_fpath):
        self.load_model(pth_fpath)
        X, ids = self.cls_model.get_X_all(type_id=self.type_id)
        pred = self(X)
        labels = pred.argmax(1).tolist()
        return labels

    @property
    def fpath_pth(self):
        raise NotImplementedError
    
    def do_train(self, pth_fpath=None, num_epochs=epochs):
        pth_fpath = pth_fpath if pth_fpath is not None else self.fpath_pth
        correct = loss = 0
        for t in range(num_epochs):
            print(f"Epoch {t+1}/{num_epochs}\n-------------------------------")
            self.train_loop()
            correct, loss = self.test_loop()
        print("Done!")
        torch.save(self.state_dict(), pth_fpath)
        print("Saved!")
        time.sleep(3)
        self.update_train_result(pth_fpath)
        return correct, loss
    
class NeuralNetwork(BaseNet, nn.Module):
    # NC = num_class
    def __init__(self, cls_model, type_id, label_list):
        super().__init__()
        self.num_label = len(label_list)

        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28*28, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, self.num_label),
        )

        self.cls_model = cls_model
        self.type_id = type_id
        # self.label_list = label_list
        self.label_dict = dict(label_list)
        self.__loss_fn = nn.CrossEntropyLoss()
        self.__optimizer = torch.optim.SGD(self.parameters(), lr=learning_rate)
        self.__data_loader = DataLoader(DbImageDatasetCommon(cls_model, type_id, label_list), batch_size=batch_size)
    



# class NumberNeuralNetwork(NeuralNetwork):
#     NC = len(DecimalNumber.TYPE_DN)
#     def __init__(self):
#         super().__init__()
#         self.flatten = nn.Flatten()
#         self.linear_relu_stack = nn.Sequential(
#             nn.Linear(28*28, 512),
#             nn.ReLU(),
#             nn.Linear(512, 512),
#             nn.ReLU(),
#             nn.Linear(512, self.NC),
#         )
    

def train_loop(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        pred = model(X)
        loss = loss_fn(pred, y)

        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

        if batch % 100 == 0:
            loss, current = loss.item(), (batch + 1) * len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")


def test_loop(dataloader, model, loss_fn):
    model.eval()
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    test_loss, correct = 0, 0

    with torch.no_grad():
        for X, y in dataloader:
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y.argmax(1)).type(torch.float).sum().item()

    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")


def train(cls_model):
    model = NeuralNetwork(len(cls_model.TYPE_DN))
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)
    train_dataset = test_dataset = DbImageDataset(cls_model)
    train_dataloader = DataLoader(train_dataset, batch_size=batch_size)
    test_dataloader = DataLoader(test_dataset, batch_size=batch_size)
    
    for t in range(epochs):
        print(f"Epoch {t+1}\n-------------------------------")
        train_loop(train_dataloader, model, loss_fn, optimizer)
        test_loop(test_dataloader, model, loss_fn)
    print("Done!")
    torch.save(model.state_dict(), f'{cls_model.__name__.lower()}.pth')
    print("Saved!")


# def train_new(cls_model, type_id, label_list, fpath):
#     nn = NeuralNetwork(cls_model, type_id, label_list)
#     correct = loss = 0
#     for t in range(epochs):
#         print(f"Epoch {t+1}\n-------------------------------")
#         nn.train_loop()
#         correct, loss = nn.test_loop()
#     print("Done!")
#     torch.save(nn.state_dict(), fpath)
#     print("Saved!")
#     nn.update_train_result(fpath)
#     return correct, loss
    
# def train_number(cls_model):
#     model = NumberNeuralNetwork()
#     loss_fn = nn.CrossEntropyLoss()
#     optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)
#     train_dataset = test_dataset = NumberDbImageDataset()
#     train_dataloader = DataLoader(train_dataset, batch_size=batch_size)
#     test_dataloader = DataLoader(test_dataset, batch_size=batch_size)
#
#     for t in range(epochs):
#         print(f"Epoch {t+1}\n-------------------------------")
#         train_loop(train_dataloader, model, loss_fn, optimizer)
#         test_loop(test_dataloader, model, loss_fn)
#     print("Done!")
#     torch.save(model.state_dict(), 'number.pth')
#     print("Saved!")        
        
            