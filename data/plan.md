Hi Dr Liu and Rui
I am grateful to have the opportunity to meet you and AI4Finance community here. It's great to see so many passionate scholars and programmers who are willing to share their knowledge and experience in the community.

To further our mission, we shall have a road map and plan for NeoFinRL, and once we completed it,  we shall share it within the community. This will bring more people to join us, keep our progress in control, more people actively involved into its development and it will be able to build a better AI4Finance ecosystem. 

I have some ideas, interesting topics related to the forex environment development so far I would like to share with you. Hopefully, this also aligns with the direction of the NeoFinRL project.

1. Environment Development
    build a abstract class for all environments.
    * implement fundamental methods for all environments.
        * inherit from gym.Env
        * define action_space and observation_space wrap to gym.Space 
        * range define and conversion.
        * balance, reward, transaction fee, penalty, and other methods.
        * multi-pair trading vector and its methods.
        * buy, sell, close, limit order and limit expiration logic.
        * sb3, eRL or any other DRL related parameters and methods.
        * common check and validation methods.
    * implement render
        * log
        * plot
        * print
        * finance analysis report 

2. model training and validation
    * remove correlated features
    * normalize features for better observation
    * add features not derived from price, such news (spark), sentiment, etc. 
    * quantify all the features and unify then into range of 0.0 - 1.0 for better training.
    * hyperparameter tuning log (use w&b or tensorboard for better visibility)

3. historical dataset/live stream 
    * maintain a historical dataset pool
    * unify data format for env API
    * data processor 
        * use pd.asfreq as base frequency to group data from any source (tick or bar) 
        * add historical data from pool, live stream, etc.
        * add necessary technical indicators
        * add correlated news, sentiment and etc

4. unit test 
    * setup unit test 
    * cicd pipeline

5. project management
    * core team setup and training
    

This is a draft. We can work together on it. I would know you thought.

Should we have a regular meeting on zoom? To more effectively communicate, we limit it to 30 mins, must have agenda/topic for each speakers. anyone can drop off at any time if the topic is not interesting to them.

Notice:
This repo is no longer maintained. All my forex enviroment development is moved to https://github.com/AI4Finance-Foundation/FinRL-Metaverse.git. Please join us there, a bigger and more active community. 

metaverse is a hottest buzzword.  