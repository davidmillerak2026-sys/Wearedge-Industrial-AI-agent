# Company Info And Compliance Intake

更新日期：2026-06-09

目标：把企业组报名必须由负责人确认的信息单独收口，避免在技术文档中猜测企业主体、联系人、证件或承诺材料。

填写原则：

- 此文件保留为模板，不填写敏感真实值。
- 最终填写版放入 `submission-assets/live-evidence/legal/company-info-filled.md`，不要提交到 Git。
- 签署版承诺材料放入 `submission-assets/live-evidence/legal/`。
- 可先运行 `python scripts/prepare_final_human_action_pack.py --json` 生成 ignored 的 `.template.md` 操作模板，再由企业负责人填写/签署为最终文件。

## 企业主体

| 字段 | 最终值 | 负责人 |
| --- | --- | --- |
| 企业名称 | TBD | 企业负责人 |
| 统一社会信用代码 | TBD | 企业负责人 |
| 注册地 | TBD | 企业负责人 |
| 企业类型 | TBD | 企业负责人 |
| 是否符合中小企业参赛要求 | TBD | 企业负责人 |
| 企业无不良记录确认 | TBD | 企业负责人 |

## 项目联系人

| 字段 | 最终值 | 负责人 |
| --- | --- | --- |
| 项目负责人姓名 | TBD | 企业负责人 |
| 手机 | TBD | 企业负责人 |
| 邮箱 | TBD | 企业负责人 |
| 备用联系人 | TBD | 企业负责人 |
| 备用联系人手机 | TBD | 企业负责人 |
| 备用联系人邮箱 | TBD | 企业负责人 |

## 团队分工

| 角色 | 姓名 | 负责内容 | 是否已确认 |
| --- | --- | --- | --- |
| 项目负责人 | TBD | 报名、商务、答辩统筹 | TBD |
| 技术负责人 | TBD | 多智能体架构、API、评估指标 | TBD |
| IT/OT 集成负责人 | TBD | Xcelerator、工易魔方、MES/QMS/EMS/CMMS 接入 | TBD |
| 边缘部署负责人 | TBD | Jetson / IPC / 本地工控机部署与端侧证据 | TBD |
| 商业负责人 | TBD | 目标客户、商业模式、ROI | TBD |
| 交付负责人 | TBD | 联合 PoC、客户试点、项目计划 | TBD |

## 知识产权确认

| 确认项 | 最终状态 | 负责人 |
| --- | --- | --- |
| 企业对参赛项目拥有自主知识产权 | TBD | 企业负责人 |
| 项目无产权纠纷 | TBD | 企业负责人 |
| 开源依赖许可证边界已核对 | TBD | 技术负责人 |
| 模型权重不提交仓库、不声明为自研基础模型 | TBD | 技术负责人 |
| 参赛材料真实、准确、可核验 | TBD | 企业负责人 |

## 需要签署或留档的文件

| 文件 | 保存路径 | 状态 |
| --- | --- | --- |
| 知识产权和无产权纠纷承诺 | `submission-assets/live-evidence/legal/ip-and-no-dispute-signed.pdf` | pending |
| 无不良记录承诺 | `submission-assets/live-evidence/legal/no-adverse-record-signed.pdf` | pending |
| 报名联系人确认 | `submission-assets/live-evidence/legal/submission-contact-confirmation.md` | pending |
| 企业信息最终填写版 | `submission-assets/live-evidence/legal/company-info-filled.md` | pending |

## 报名系统人工字段

在 `docs/submission/registration-fields.md` 中复制技术文本前，先完成以下人工字段：

- 企业名称
- 统一社会信用代码
- 企业注册地址
- 项目负责人姓名、手机、邮箱
- 团队成员和职位
- 知识产权承诺
- 无不良记录承诺
- 是否同意展示、宣传、路演等报名条款
