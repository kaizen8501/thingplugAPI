# ThingPlug API for Python

본 저장소는 ThingPlug를 사용하기 위한 Python API를 제공하며, 해당 API를 사용하기 위한 예제를 포함하고 있다.
본 프로젝트는 Python 2.x 문법을 기반으로 작성되었으며, ThingPlug를 사용하면서 필요한 기능들을 하나씩 추가할 예정이다.


## Examples
- Login
```Windows
$ login.py -u <user_id> -p <user_password>
```
- Get Device List
```Windows
$ get_device_list.py -u <user_id> -p <user_password>
```
- Get Latest Data
```Windows
$ get_latest_data.py -u <user_id> -p <user_password> -n <node_id> -c <container_name>
```
- Create Subscription
```Windows
$ create_subscription.py <user_id> -p <user_password> -n <node_id> -c <container_name> -s <subscription_name> -nu <notification_uri>
```

- Retrieve Subscription
```Windows
$ create_subscription.py <user_id> -p <user_password> -n <node_id> -c <container_name> -s <subscription_name>
```

- Delete Subscription
```Windows
$ create_subscription.py <user_id> -p <user_password> -n <node_id> -c <container_name> -s <subscription_name>
```

**Step 1.** Update tools.

```
pip install -r requirements.txt
```