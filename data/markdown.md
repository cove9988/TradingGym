have you think about two steps traning DRL?
    since intuitively most of time, the bot (model) shall do nothing just observe.
    so the first stage, we shall train our model by doing nothing with rewards. so the model will output all actions with the same probability to do nothing.

    the second stage, we shall train our model by high epsilon with normal rewards, since PPO is update the model slowly, hopefully it can get some good strategy upgraded of the model.

How to tune hyperparameters?

1. make sure the model is good enough to learn the task.
   * choose the simplest mode and data possible.
   * once model runs, overfit a single batch and reproduce result.
2. Explore before exploit.
   * explore by playing the game.
   * swee[ pver hyper-parameters: use coarse-fine random search.
3. Ask yourself: Am I overfitting or underfitting?
   * make your model bigger if you underfit.
   * make your model smaller if you overfit.
   * how to train the model?
   * how to evaluate the model?
   * how to test the model?
   * how to improve the model?  

Hope this message reach you well. I am the developer of the forex gym environment project (https://github.com/AI4Finance-Foundation/FinRL-Metaverse/tree/main/neo_finrl/env_fx_trading) . The initial version passed basic unit test. Now we are working on the model training. Since the approach of forex is different from stock, we are facing some challenges of parallel training and hyper-parameter tuning. I know you have a lot of experience in this area. I will try to help you. Would you like to join us?

A couple of developers approach me and show me their interest in the forex project. Just wondering how to leverage and build a core team for the project. Would you like to have a chat sometime?

In a continuous action space, your agent must output some real-valued number, possibly in multiple dimensions. A good example is the MountianCar problem where you must output the force to apply as a real number.

There are a few ways continuous control can be tackled:

Just break the output up into segments, and treat each one as a discrete action. This doesn't work if extreme precision is required (and often is in robotics) or if space if very large (or potentially infinite)

Output parameters to a parametric model, i.e. mean and standard deviation to a normal distribution, then sample from it. I'm not so familiar with this one, but I beleive it's used to encourage exploration.

Directly output the value you want. i.e. in the case of a neural network, instead of outputting the log-probabilities for each action, just output the real-valued directly.
