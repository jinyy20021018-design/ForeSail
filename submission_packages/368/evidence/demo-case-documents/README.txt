ForeSail 演示案例——使用一笔按常见中国出口业务格式制作的合成 CIF/LC 交易，演示系统如何研判真实发生的 2026 年霍尔木兹海峡危机对具体航线、合同义务和信用证期限的潜在影响。

交易概况
  卖方（我方）：Shanghai Solaris PV Co., Ltd.（上海 Solaris 光伏有限公司）
  买方：Gulf Renewable Energy Trading LLC（迪拜）
  货物：15,000 块太阳能光伏组件（8.1 MWp），总价 1,890,000 美元，CIF 杰贝阿里（Incoterms 2020）
  航线：上海 -> 马六甲海峡 -> 印度洋 -> 霍尔木兹海峡 -> 杰贝阿里
  船舶：GULF HORIZON；预计离港（ETD）：2026 年 8 月 28 日；预计抵达杰贝阿里（ETA）：2026 年 9 月 15 日；
        最迟装运日：2026 年 9 月 5 日；信用证到期日：2026 年 9 月 30 日。

真实危机背景与演示数据边界
  危机背景来自公开报道：2026 年霍尔木兹海峡通行曾受到严重限制，波斯湾内船舶积压，航运公司暂停或调整相关服务，
  并出现战争险、燃油及应急附加费上升。“约 138 艘集装箱船、约 47 万 TEU 受困”和“据报道每艘船超过
  100 万美元的通行费用”等数字，均采用下列公开来源的报道口径。

  为让评委在不同日期稳定复现完整工作流，backend/app/data/curated_events.json 并非实时事件流，而是团队依据上述
  公开背景整理的结构化演示场景。每条记录的 real_basis 和 sources 用于说明真实背景及来源；但事件编号、
  GULF HORIZON 船名、与本演示交易对应的精确 ETA 和延误天数、具体港口后果以及 expected_classification
  均为合成测试字段，不表示公开来源曾报道该船舶或该笔交易。

  event_time_offset_days、old_eta_offset_days 和 new_eta_offset_days 会由 event_date_anchor.py 在运行时相对当天
  重新计算，使演示事件保持在可测试时间窗口内。因此，这些记录应理解为“基于真实公开报道整理的可复现演示事件”，
  而不是实时抓取的真实船舶事件。

演示场景用于研判的潜在影响（并非已发生事实）
  1. 履约与运输：若承运人无法通过霍尔木兹海峡或无法挂靠杰贝阿里，卖方可能需要改港、重新订舱或协调替代运输，
     并面临合同履约争议。
  2. 成本：CIF 条款下卖方负责安排并支付至指定目的港的主运输；战争险附加费、应急附加费、改港或绕航费用可能增加
     卖方的运输成本，具体仍取决于运输合同及费用条款。
  3. 货物风险与保险：CIF 下货物灭失或损坏风险通常在装运港装上船时转移给买方，但卖方仍负有安排约定运输和提供
     最低保险的义务；战争险除外或保额不足可能形成买方货物风险及卖方保险履约问题。
  4. 付款：若装运前的订舱取消或港口中断导致错过 2026 年 9 月 5 日的最迟装运日，可能形成信用证不符点并影响卖方收款。

来源
  - https://www.seavantage.com/blog/strait-of-hormuz-crisis-2026-shipping-disruption-timeline
  - https://www.flexport.com/blog/middle-east-escalation-disrupts-global-ocean-and-air-freight-networks/
  - https://unctad.org/news/hormuz-reopening-may-calm-markets-vulnerable-economies-face-lasting-consequences

工程说明
  当前系统已不再依赖 relevance_engine 中固定的 WATCHED_REGIONS 列表限制区域覆盖。watch_profile_service 会调用
  route_region_service.merge_watched_route_regions，根据每笔 Case 的航线、装货港、卸货港和最终目的地动态生成
  watched_route_regions，并通过 port_registry 补充港口所属区域。

  对当前霍尔木兹演示案例，系统可生成 Shanghai、Strait of Malacca、Strait of Hormuz、Jebel Ali、
  East China Sea、Persian Gulf 和 Dubai 等监控区域；上传材料中的航线还明确包含 Indian Ocean。
  CORRIDOR_ALIASES 已支持 Hormuz、Persian Gulf、Gulf of Oman，以及 Indian Ocean 与 Arabian Sea 等文本别名，
  因此霍尔木兹及波斯湾事件能够通过航线、区域、港口或事件文本匹配参与相关性评分。

  DEFAULT_WATCHED_REGIONS = {East China Sea、South China Sea、Bay of Bengal、Bangladesh} 仅在 Case 没有可用航线
  或港口区域时作为兜底，并不代表系统当前的区域上限。
