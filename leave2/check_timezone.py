from app.models.jwt_models import get_local_datetime
from datetime import datetime
import pytz

# 測試本地時間
local_time = get_local_datetime()
utc_time = datetime.utcnow()
Ho_Chi_Minh = pytz.timezone('Asia/Ho_Chi_Minh')
expected_time = datetime.now(Ho_Chi_Minh).replace(tzinfo=None)

print(f"本地時間: {local_time}")
print(f"UTC 時間: {utc_time}")
print(f"預期時間: {expected_time}")