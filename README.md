## 1.使用
```
  python main.py
```
## 2.代理配置
```
若无代理，注释main.py中关于配置的代码
os.environ["http_proxy"] = "http://127.0.0.1:10809"
os.environ["https_proxy"] = "http://127.0.0.1:10809"
```
## 3.依赖包配置
```
pip install -r requirements.txt
```
## 4.参数配置
```
修改config.ini文件

1. private_key     配置私钥
2. is_auto_buy     是否自动买入(0: 不买入, 1: 自动买入)
3. is_auto_sell    是否自动卖出(0: 不卖出, 1: 自动卖出)
4. pool_size       设置池子买入条件(大于多少时买入)
5. buy_amount      设置买入数量(单位(sol))
6. gap_time        设置买入后多久时间卖出(int, 单位(秒))
```
# 感谢您的捐赠！！！！！
![微信图片_20240321040708](https://github.com/dev-cerber/solana_swap_sniper/assets/35053590/474f79b3-3f6f-453e-986b-f44c2f9015b5)
