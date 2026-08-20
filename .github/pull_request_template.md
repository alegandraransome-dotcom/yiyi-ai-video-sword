## 变更范围

- [ ] 只修改了声明范围内的模块
- [ ] 更新了迁移账本或说明了无需更新的理由
- [ ] 保持 `00 + 08` 常驻与薇/恒隔离
- [ ] 没有把 Module 09、原始上游 Skill 或失效平台规则带入正常 Runtime

## 验证

- [ ] `yi validate .`
- [ ] `python -m unittest discover -s tests -v`
- [ ] 两次 `.yios` 构建字节一致
- [ ] 涉及行为能力时，已记录对应 Beta-3 人工回归结果
