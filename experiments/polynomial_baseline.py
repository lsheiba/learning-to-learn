import numpy as np
import os
import matplotlib.pyplot as plt
from gym_learning_to_learn.datasets import polynomial
from gym_learning_to_learn.utils.np_utils import generate_or_load_dataset
from keras.layers import Dense, LeakyReLU, Input, Dropout
from keras.models import Model
from keras.optimizers import SGD
from learning_to_learn.normalization import LayerNormalization
import pandas as pd


def create_model(input_dim, output_dim, nch, dropout, layernorm):
    x = Input((input_dim,))
    # reg = lambda: l1l2(1e-7, 1e-7)
    reg = lambda: None
    h = Dense(nch, W_regularizer=reg())(x)
    if layernorm:
        h = LayerNormalization()(h)
    if dropout > 0:
        h = Dropout(dropout)(h)
    h = LeakyReLU(0.2)(h)
    h = Dense(nch, W_regularizer=reg())(h)
    if layernorm:
        h = LayerNormalization()(h)
    if dropout > 0:
        h = Dropout(dropout)(h)
    h = LeakyReLU(0.2)(h)
    h = Dense(nch, W_regularizer=reg())(h)
    if layernorm:
        h = LayerNormalization()(h)
    if dropout > 0:
        h = Dropout(dropout)(h)
    h = LeakyReLU(0.2)(h)
    y = Dense(output_dim, W_regularizer=reg())(h)
    model = Model(x, y)
    return model


def trials(path, create_opt, nch, dropout, layernorm):
    if os.path.exists(path):
        return
    nb_epoch = 1000
    nb_trial = 10
    test_set = "output/polynomial/test-set.npz"
    (x_train, y_train), (x_val, y_val), (x_test, y_test) = generate_or_load_dataset(test_set, polynomial.load_data)
    results = {}
    for i in range(nb_trial):
        model = create_model(x_train.shape[1], y_train.shape[1], nch=nch, dropout=dropout, layernorm=layernorm)
        opt = create_opt()
        model.compile(opt, 'mean_squared_error')
        history = model.fit(x_train, y_train, validation_data=(x_val, y_val), nb_epoch=nb_epoch).history
        results["loss_{:03d}".format(i)] = history["loss"]
        results["val_loss_{:03d}".format(i)] = history["val_loss"]
    df = pd.DataFrame(results)
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    df.to_csv(path)


def graph(path):
    assert os.path.exists(path)
    imgpath = os.path.join(os.path.dirname(path), os.path.basename(path) + ".png")
    #if os.path.exists(imgpath):
    #    return
    if not os.path.exists(os.path.dirname(imgpath)):
        os.makedirs(os.path.dirname(imgpath))
    df = pd.read_csv(path)
    values = df.values
    nb_trial = (values.shape[1]-1)/2
    nb_epoch = values.shape[0]
    fig = plt.figure()
    for i in range(nb_trial):
        plt.plot(np.arange(nb_epoch), np.log(values[:, 1+i]), label="Train {}".format(i), c="b")
        plt.plot(np.arange(nb_epoch), np.log(values[:, 1+i+nb_trial]), label="Val {}".format(i), c="g")
    fig.savefig(imgpath)
    plt.close(fig)



def baseline(path, create_opt, nch, dropout, layernorm):
    trials(path, create_opt, nch, dropout, layernorm)
    graph(path)


def main():
    basepath = "output/polynomial"
    models = []
    for name, opt in [("sgd-1e1", lambda:SGD(1e-1)),("sgd-1e2", lambda:SGD(1e-2)),("sgd-1e3", lambda:SGD(1e-3)),("sgd-1e4", lambda:SGD(1e-4)),("sgd-1e5", lambda:SGD(1e-5))]:
        for nch in [64, 128, 256, 512, 1024]:
            for dropout in [0,0.5]:
                for layernorm in [False, True]:
                    path = os.path.join(basepath, "polynomial-{}-{}".format(nch, name))
                    if dropout > 0:
                        path += "-dropout"
                    if layernorm:
                        path += "-layernorm"
                    path += ".csv"
                    baseline(path, opt, nch=nch, dropout=dropout, layernorm=layernorm)
                    models.append(path)
    #baseline("output/polynomial/baseline-sgd-1e1.csv", lambda: SGD(1e-1))
    #baseline("output/polynomial/baseline-sgd-1e2.csv", lambda: SGD(1e-2))
    #baseline("output/polynomial/baseline-sgd-1e3.csv", lambda: SGD(1e-3))
    #baseline("output/polynomial/baseline-sgd-1e4.csv", lambda: SGD(1e-4))
    # baseline("output/polynomial/baseline-sgd-1e2-decay-1e3.csv", lambda: SGD(1e-2, decay=1e-3))
    # baseline("output/polynomial/baseline-sgd-1e2-decay-1e1.csv", lambda: SGD(1e-2, decay=1e-1))


if __name__ == "__main__":
    main()