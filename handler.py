import boto3
import datetime
import distutils.util
import jpholiday
import logging
import os
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ['REGION']
# リージョン単位の指定
AUTO_STOP = os.environ['AUTO_STOP']
AUTO_START = os.environ['AUTO_START']
STOP_HOLIDAY = os.environ['STOP_HOLIDAY']
# インスタンスの指定
NO_STOP_TAG = os.environ['NO_STOP_TAG']
NO_START_TAG = os.environ['NO_START_TAG']

ec2 = boto3.client('ec2', region_name=REGION)


# 対象のEC2のリストの作成だけを行うフラグを返す
def only_check_target_ec2(event):
    logger.info("start function: {}".format(sys._getframe().f_code.co_name))

    list_flag = False
    for key, val in event.items():
        if key == "LIST" and val == "True":
            list_flag = True
    return list_flag


# 自動起動/停止の設定確認
def check_auto_stop_start(action):
    logger.info("start function: {}".format(sys._getframe().f_code.co_name))

    auto_stop_start = True
    if action == 'STOP' and AUTO_STOP == 'False':
        auto_stop_start = False
    elif action == 'START' and AUTO_START == 'False':
        auto_stop_start = False

    logger.info('AUTO_STOP/AUTO_START: {}'.format(auto_stop_start))
    return auto_stop_start


# EC2対象インスタンスリストの作成
# 対象のEC2のリストを作成
def get_target_ec2(action):
    logger.info("start function: {}".format(sys._getframe().f_code.co_name))

    if action == "STOP":
        status = ['running']
    elif action == "START":
        status = ['stopped']

    target_ec2_list = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': status}
        ]
    )
    return target_ec2_list


# 対象インスタンスからIDを抽出
def get_ec2_id(target_ec2_list):
    logger.info("start function: {}".format(sys._getframe().f_code.co_name))

    ec2_id_list = []
    for reservation in target_ec2_list['Reservations']:
        for instance in reservation['Instances']:
            no_stop_flg = False
            for tag in instance['Tags']:
                if tag['Key'] == NO_STOP_TAG and tag['Value'] == 'True':
                    no_stop_flg = True
        if no_stop_flg is False:
            ec2_id_list.append(instance['InstanceId'])
    return ec2_id_list


# 自動起動/停止の設定確認
def change_ec2_status(action, ec2_id_list):
    logger.info("start function: {}".format(sys._getframe().f_code.co_name))

    proccessed_list = []
    if action == "STOP":
        result = ec2.stop_instances(InstanceIds=ec2_id_list)
        logger.info("ec2 stop command result: {}" .format(result))
        for instance in result['StoppingInstances']:
            proccessed_list.append(instance['InstanceId'])
    elif action == "START":
        result = ec2.start_instances(InstanceIds=ec2_id_list)
        logger.info("ec2 start command result: {}".format(result))
        for instance in result['StartingInstances']:
            proccessed_list.append(instance['InstanceId'])
    return proccessed_list


# 土日祝日の判定
def is_holiday():
    logger.info("start function: {}".format(sys._getframe().f_code.co_name))

    today = datetime.date.today() + datetime.timedelta(days=0)
    logger.info('today: {}'.format(today))
    return jpholiday.is_holiday(today)


# メインの処理
def lambda_handler(event, context):
    logger.info("start lambda function: {}".format(context.function_name))

    try:
        return_values = {}
        list_flag = only_check_target_ec2(event)

        if distutils.util.strtobool(STOP_HOLIDAY):
            holiday_flag = is_holiday()
            logging.info('is_holiday: {}'.format(holiday_flag))

            if holiday_flag:
                return return_values

        if 'ACTION' not in event:
            raise KeyError(
                "The key [proccess_target] does not exist in event.")

        action = event['ACTION']
        if action not in ["STOP", "START"]:
            raise KeyError("PROCCESS_TARGET must be one of [STOP,START]")

        return_values['proccess_target'] = action
        logger.info('proccess_target: {}'.format(action))

        target_ec2_list = get_target_ec2(action)
        ec2_id_list = get_ec2_id(target_ec2_list)
        return_values['target_ec2_id'] = ec2_id_list
        logger.info(
            '{} instance list: {}'.format(
                action,
                str(ec2_id_list)))
        if ec2_id_list:
            if list_flag:
                logger.info(
                    'List flag is true. starting/stopping proccess will be passing.')
            else:
                change_ec2_status(action, ec2_id_list)
            logger.info('Proccessing has been succeeded.')
            return return_values
        else:
            logger.info('target instances are nothing')
            return return_values
    except Exception as e:
        logger.error("error ocured {}".format(e))
        return_values['error_desc'] = str(e)
        return return_values
