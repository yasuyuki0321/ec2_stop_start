# 処理概要
- RDSの停止/起動を行うLambda関数  
- 処理はCloudwatch Eventsから実行される
- 処理の実行時間はCloudwatch Eventsで設定する
  - イベント名はmaint-rds-stop/maint-rds-start
  - デフォルトでは両イベントとも無行になっているので、使用するためには、実行時間確認後有効化する
- 停止起動の挙動はLambdaの環境変数およびインスタンスのタグで制御が可能  

# インストール方法
Serverless Frameworkを使用してインストールを行う  
Serverless Frameworkがインストールされていない場合には↓に従いインストールする
https://serverless.com/framework/docs/getting-started/

### プログラムの取得
```
git clone rds-stop-start
cd rds-stop-start
```

### serverless.ymlのパラメータ変更
Lambdaにデプロイするモジュール等をUpするS3バケットを指定
```
  deploymentBucket:
    name: serverless-deployment-173212653244
```
  
$PATHにpythonが含まれていない場合に指定が必要pyenvを使用している場合など)
```
  pythonRequirements:
    pythonBin: /Users/kikuchi/.pyenv/shims/python3.7
```

### Serverless Frameworkのpluginのインストール
```
sls plugin install -n serverless-prune-plugin
sls plugin install -n serverless-python-requirements
```

### direnv等で環境変数にAWSのアクセスキー、シークレットキーを設定する
```
export AWS_ACCESS_KEY_ID=abc123
export AWS_SECRET_ACCESS_KEY=xyz789
export AWS_DEFAULT_REGION=ap-northeast-1
```

### プログラムのデプロイ
```
sls deploy -v
```


# デフォルトの動作
## Stop
- RDSにNoStopのタグが付いていない場合には、全てのRDSは停止される
- RDSを停止させたくない場合には、RDSにTags: NoStop、Value: True のタグを付ける

## Start
- RDSにNoStartのタグが付いていない場合には、全てのRDSは起動される
- 全てのRDSを起動しない場合には、Lambdaの環境変数AUTO_STARTをFalseに設定、もしくはCloudwatch Events(maint-rds-start)をdisableに設定する
- 一部のRDSのみ起動しない場合には、起動しないRDSにTags: NoStart、Value: True のタグを付ける

## Stop/Start
- 土日、祝祭日はRDSの停止/起動処理は行わない
- 土日もRDSの停止/起動処理を行う場合には、Cloudwatch Eventsの設定を変更する
- 祝祭日もRDSの停止/起動処理を行う場合には、Lambda環境変数のSTOP_HOLIDAYをFalseに設定する

# Lambda環境変数およびRDSタグ
## Lambda環境変数  
| 環境変数|デフォルト|説明 |
|:---|:---|:---|
|REGION|ap-northeast-1|対象のAWSリージョン|
|AUTO_STOP|True|RDS停止処理を実行するかしないかを指定|
|AUTO_START|True|RDS起動処理を実行するかしないかを指定|
|STOP_HOLIDAY|True|祝祭日にRDSの停止/起動処理を実行するかを指定|
|NO_STOP_TAG|NoStop|停止させたくないRDSに付与するタグ名|
|NO_START_TAG|NoStart|起動させたくないRDSに付与するタグ名|
|TZ|Asia/Tokyo|Lambdaのタイムゾーンを設定|

## RDSタグ  
|タグ名| 説明 |
|:---|:---|
|NoStop|Value: Trueを設定することで、RDSを停止させない|
|NoStart|Value: Trueを設定することで、RDSを起動させない|
※タグ名はLambd関数(NO_STOP_TAG/NO_START_TAG)の設定を変更することで変更可能