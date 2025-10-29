# Sui Bridge FrontRunner

自动抢跑Sui Bridge限额情况。

我本以为是在Sui侧的Limit（如尝试从sui的object查看），但实际上是以太坊侧claim时的Limit，被eth上的桥合约控制。

因为被 incrediblez7.eth 给包场了，我本金少gas没法和他竞争就只能干脆给大家开源了。

Automatically frontrun the Sui Bridge limit status.

It was thought to be the Limit on the Sui side (such as [trying to view from Sui's object](./sui.py)), but in fact it is the Limit during claim on the Ethereum side.

## Usage

How to find your tx nonce 
找交易序号方法：
![How to find your tx nonce](./HowToFindNonce.png)

1. Suggest to use uv
2. Install dependencies: `uv pip install -r requirements.txt`
3. Edit the nonce `frontrunner.py`, and set the PRIVATE_KEY environment variable.
4. Run `frontrunner.py` to frontrun.

随手写的代码，欢迎修改。目前只能抢一个交易的跑，要多个可以multicall或者incrediblez7.eth一样自己做合约。
当前会自动帮你获取claim需要的message payload和对应Sui committees对你这笔跨链的signature。

1. 建议使用uv
2. 安装依赖：`uv pip install -r requirements.txt`
3. 编辑`frontrunner.py`来修改nonce为你的跨链交易，并设置PRIVATE_KEY环境变量。
4. 运行`uv run frontrunner.py`来抢跑。

## FAQ

Q: 如何提前得知下个小时00分会有多少解锁？

A: 懒得写代码了建议肉眼看 https://etherscan.io/tokentxns?a=0x312e67b47a2a29ae200184949093d92369f80b53&p=2 如图，方向为out的23hrs ago的就是下个00分会解锁的金额
<img width="2940" height="1656" alt="image" src="https://github.com/user-attachments/assets/d5d96d42-c333-4c43-84aa-34aee50872f6" />




## Disclaimer

This is just a small tool I use to bridge suiUSDT that has been depeg due to MMT & Buidlpad activities from Sui to ETH. I am not responsible for any losses that may occur as a result of using this code.

这只是我用来将由于MMT & Buidlpad活动而脱钩的suiUSDT从Sui跨回ETH的一个小工具。我不对任何由于使用此代码而导致的损失负责。

顺便吐槽一下这机制真离谱，一个大户就能包圆了整个桥。还不如像sonic这些给个确定的delay。
