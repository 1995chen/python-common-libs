# TemplateJsonEncoder 使用说明

## 说明

该库可以实现了Json序列化需要的Encoder

## 代码示例

```python

import json

from template_json_encoder import TemplateJSONEncoder


json.dumps(1, default=TemplateJSONEncoder().default)
```

