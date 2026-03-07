# -*- coding: utf-8 -*-
"""
南京/全国通用 - 年终一次性奖金多年最优提取计算工具 (CLI 命令行版)
作者：于海翔
版本：2026.3

功能：
    1. 计算年终奖单独计税 vs 并入综合所得的最优方案
    2. 支持两年联动优化（奖金递延/提前），寻找全局最低税负
    3. 内置 2026 年最新个税专项附加扣除标准

================================================================================
快速使用示例：
================================================================================

# 场景 1：基础计算（两年收入相同）
python3 tax_optimizer.py \\
    --monthly-salary 15000 \\
    --annual-bonus 80000 \\
    --monthly-social-security 2000 \\
    --monthly-housing-fund 2000 \\
    --monthly-special-deduction 4500

# 场景 2：明年收入有变化（如涨薪、奖金变化）
python3 tax_optimizer.py \\
    --monthly-salary 15000 \\
    --annual-bonus 80000 \\
    --monthly-social-security 2000 \\
    --monthly-housing-fund 2000 \\
    --monthly-special-deduction 4500 \\
    --year2-monthly-salary 16000 \\
    --year2-annual-bonus 100000

# 场景 3：查看完整帮助和扣除标准说明
python3 tax_optimizer.py --help

================================================================================
"""

import argparse
import sys
from typing import Dict, Tuple

# ==============================================================================
# 税率表配置
# ==============================================================================

class TaxRates:
    """个税税率表配置"""
    
    # 综合所得税率表 (年应纳税所得额)
    COMPREHENSIVE_RATES = [
        (0, 36000, 0.03, 0, "3%"),
        (36000, 144000, 0.10, 2520, "10%"),
        (144000, 300000, 0.20, 16920, "20%"),
        (300000, 420000, 0.25, 31920, "25%"),
        (420000, 660000, 0.30, 52920, "30%"),
        (660000, 960000, 0.35, 85920, "35%"),
        (960000, float('inf'), 0.45, 181920, "45%")
    ]
    
    # 年终奖单独计税率表
    BONUS_RATES = [
        (0, 36000, 0.03, 0),
        (36000, 144000, 0.10, 210),
        (144000, 300000, 0.20, 1410),
        (300000, 420000, 0.25, 2660),
        (420000, 660000, 0.30, 4410),
        (660000, 960000, 0.35, 7160),
        (960000, float('inf'), 0.45, 15160)
    ]

# ==============================================================================
# 税务计算器
# ==============================================================================

class TaxCalculator:
    """个税计算核心逻辑"""
    
    @staticmethod
    def calculate_comprehensive_tax(taxable_income: float) -> float:
        """计算综合所得税"""
        if taxable_income <= 0:
            return 0.0
        for low, high, rate, quick_deduction, _ in TaxRates.COMPREHENSIVE_RATES:
            if low < taxable_income <= high:
                return taxable_income * rate - quick_deduction
        return 0.0
    
    @staticmethod
    def calculate_bonus_tax_separate(bonus: float) -> float:
        """计算年终奖单独计税"""
        if bonus <= 0:
            return 0.0
        for low, high, rate, quick_deduction in TaxRates.BONUS_RATES:
            if low < bonus <= high:
                return bonus * rate - quick_deduction
        return 0.0
    
    @staticmethod
    def get_tax_bracket_info(taxable_income: float) -> Dict:
        """获取应纳税所得额的税率档位信息"""
        if taxable_income <= 0:
            return {
                'bracket_rate': '0%',
                'bracket_low': 0,
                'bracket_high': 36000,
                'excess_amount': 0,
                'excess_percent': 0,
                'income': 0
            }
        
        for low, high, rate, _, rate_str in TaxRates.COMPREHENSIVE_RATES:
            if low < taxable_income <= high:
                excess = taxable_income - low
                if high != float('inf'):
                    percent = excess / (high - low) * 100
                else:
                    percent = 0
                return {
                    'bracket_rate': rate_str,
                    'bracket_low': low,
                    'bracket_high': high,
                    'excess_amount': excess,
                    'excess_percent': percent,
                    'income': taxable_income
                }
        return None
    
    @staticmethod
    def calculate_year_tax_with_split(
        annual_salary: float, 
        annual_deductions: float, 
        bonus_total: float,
        bonus_separate: float
    ) -> Tuple[float, str, float]:
        """计算单年税额（支持奖金分拆）"""
        bonus_separate = max(0, min(bonus_separate, bonus_total))
        bonus_merged = bonus_total - bonus_separate
        
        comprehensive_taxable = annual_salary + bonus_merged - annual_deductions
        tax_comprehensive = TaxCalculator.calculate_comprehensive_tax(comprehensive_taxable)
        tax_bonus = TaxCalculator.calculate_bonus_tax_separate(bonus_separate)
        
        total_tax = tax_comprehensive + tax_bonus
        
        if bonus_separate <= 0:
            method = "全部并入综合所得"
        elif bonus_merged <= 0:
            method = "全部单独计税"
        else:
            method = f"分拆：{bonus_separate:,.0f} 单独 + {bonus_merged:,.0f} 并入"
        
        return total_tax, method, comprehensive_taxable

# ==============================================================================
# 优化引擎
# ==============================================================================

class OptimizationEngine:
    """多年奖金优化引擎（支持分拆 + 递延）"""
    
    def __init__(self):
        self.calculator = TaxCalculator()
    
    def optimize_two_years(self, year1_data: Dict, year2_data: Dict) -> Dict:
        """执行两年联动优化"""
        s1 = year1_data['annual_salary']
        d1 = year1_data['annual_deductions']
        b1 = year1_data['bonus']
        
        s2 = year2_data['annual_salary']
        d2 = year2_data['annual_deductions']
        b2 = year2_data['bonus']
        
        total_bonus_pool = b1 + b2
        
        orig_tax1, orig_method1, orig_comp1 = self.calculator.calculate_year_tax_with_split(s1, d1, b1, b1)
        orig_tax2, orig_method2, orig_comp2 = self.calculator.calculate_year_tax_with_split(s2, d2, b2, b2)
        orig_total_tax = orig_tax1 + orig_tax2
        
        best_config = {}
        min_total_tax = float('inf')
        
        shift_step = 1000
        split_step = 1000
        
        print(f"🔍 正在搜索最优方案...（奖金池总计 {total_bonus_pool:,.0f} 元）")
        print(f"   搜索范围：递延 0-{b1:,.0f} 元，分拆 0-当年奖金 元")
        print(f"   步长精度：{shift_step} 元\n")
        
        for shift in range(0, int(b1) + 1, shift_step):
            current_b1_total = b1 - shift
            current_b2_total = b2 + shift
            
            for split1 in range(0, int(current_b1_total) + 1, split_step):
                for split2 in range(0, int(current_b2_total) + 1, split_step):
                    
                    tax1, method1, comp1 = self.calculator.calculate_year_tax_with_split(
                        s1, d1, current_b1_total, split1
                    )
                    tax2, method2, comp2 = self.calculator.calculate_year_tax_with_split(
                        s2, d2, current_b2_total, split2
                    )
                    
                    total_tax = tax1 + tax2
                    
                    if total_tax < min_total_tax:
                        min_total_tax = total_tax
                        best_config = {
                            'shift_amount': shift,
                            'year1_bonus_total': current_b1_total,
                            'year1_bonus_separate': split1,
                            'year1_bonus_merged': current_b1_total - split1,
                            'year1_tax': tax1,
                            'year1_method': method1,
                            'year1_comp_taxable': comp1,
                            'year2_bonus_total': current_b2_total,
                            'year2_bonus_separate': split2,
                            'year2_bonus_merged': current_b2_total - split2,
                            'year2_tax': tax2,
                            'year2_method': method2,
                            'year2_comp_taxable': comp2,
                            'total_tax': min_total_tax
                        }
        
        return {
            'original': {
                'year1_tax': orig_tax1,
                'year1_method': orig_method1,
                'year1_bonus': b1,
                'year1_comp_taxable': orig_comp1,
                'year2_tax': orig_tax2,
                'year2_method': orig_method2,
                'year2_bonus': b2,
                'year2_comp_taxable': orig_comp2,
                'total_tax': orig_total_tax
            },
            'optimized': best_config,
            'saving': orig_total_tax - min_total_tax
        }

# ==============================================================================
# 命令行参数解析
# ==============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    
    parser = argparse.ArgumentParser(
        prog='tax_optimizer.py',
        description='🧮 南京/全国通用 - 年终一次性奖金多年最优提取计算工具',
        epilog='''
================================================================================
💡 专项附加扣除标准参考 (2026 年最新版)
================================================================================

请将以下符合您情况的金额相加，填入 --monthly-special-deduction 参数：

┌─────────────────────────────────────────────────────────────────────────────┐
│  扣除项目              标准金额 (每月)          说明                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. 子女教育           2000 元/孩              3 岁至博士研究生教育          │
│  2. 3 岁以下婴幼儿      2000 元/孩              0-3 岁婴幼儿照护              │
│  3. 赡养老人           3000 元/月              独生子女 3000，非独生分摊      │
│  4. 住房租金 (南京)     1500 元/月              省会城市标准，有房贷则填 0     │
│  5. 住房贷款利息        1000 元/月              首套住房，有租金则填 0         │
│  6. 继续教育           400 元/月               学历教育，或 3600 元/年 (证书)  │
│  7. 大病医疗           据实结算                通常次年汇算，平时可填 0       │
└─────────────────────────────────────────────────────────────────────────────┘

📌 计算示例：
   南京租房 (1500) + 独生子女赡养老人 (3000) + 1 个孩子 (2000) = 6500 元/月
   则参数填写：--monthly-special-deduction 6500

⚠️ 注意事项：
   1. 住房租金和住房贷款利息只能二选一
   2. 本工具基于现行个税政策（年终奖单独计税优惠延续至 2027 年底）
   3. 奖金分拆发放需公司财务/HR 配合
   4. 社保基数与上年度平均工资挂钩，分拆/递延可能影响明年社保扣款
   5. 本工具仅供参考，实际纳税以税务局汇算清缴为准

================================================================================
        ''',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    year1_group = parser.add_argument_group('📅 第 1 年收入参数 (必填)')
    year1_group.add_argument('--monthly-salary', type=float, required=True, metavar='金额',
        help='第 1 年每月税前工资收入 (元)')
    year1_group.add_argument('--annual-bonus', type=float, required=True, metavar='金额',
        help='第 1 年预计年终奖金总额 (元)')
    year1_group.add_argument('--monthly-social-security', type=float, required=True, metavar='金额',
        help='第 1 年每月社保个人缴纳部分 (元)')
    year1_group.add_argument('--monthly-housing-fund', type=float, required=True, metavar='金额',
        help='第 1 年每月公积金个人缴纳部分 (元)')
    year1_group.add_argument('--monthly-special-deduction', type=float, required=True, metavar='金额',
        help='第 1 年每月专项附加扣除总额 (元)')
    
    year2_group = parser.add_argument_group('📅 第 2 年收入参数 (选填)')
    year2_group.add_argument('--year2-monthly-salary', type=float, default=None, metavar='金额',
        help='第 2 年预计每月税前工资 (元)')
    year2_group.add_argument('--year2-annual-bonus', type=float, default=None, metavar='金额',
        help='第 2 年预计年终奖金总额 (元)')
    year2_group.add_argument('--year2-monthly-social-security', type=float, default=None, metavar='金额',
        help='第 2 年预计每月社保个人缴纳 (元)')
    year2_group.add_argument('--year2-monthly-housing-fund', type=float, default=None, metavar='金额',
        help='第 2 年预计每月公积金个人缴纳 (元)')
    year2_group.add_argument('--year2-monthly-special-deduction', type=float, default=None, metavar='金额',
        help='第 2 年预计每月专项附加扣除 (元)')
    
    return parser

def validate_arguments(args: argparse.Namespace) -> None:
    """验证参数合理性"""
    errors = []
    if args.monthly_salary <= 0:
        errors.append("❌ 每月工资必须大于 0")
    if args.annual_bonus < 0:
        errors.append("❌ 年终奖不能为负数")
    if args.monthly_social_security < 0:
        errors.append("❌ 社保缴纳不能为负数")
    if args.monthly_housing_fund < 0:
        errors.append("❌ 公积金缴纳不能为负数")
    if args.monthly_special_deduction < 0:
        errors.append("❌ 专项附加扣除不能为负数")
    
    if errors:
        print("参数验证失败：")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)

def prepare_year_data(args: argparse.Namespace, year: int) -> Dict:
    """根据命令行参数构建年度数据"""
    if year == 1:
        monthly_salary = args.monthly_salary
        annual_bonus = args.annual_bonus
        monthly_social = args.monthly_social_security
        monthly_housing = args.monthly_housing_fund
        monthly_deduction = args.monthly_special_deduction
    else:
        monthly_salary = args.year2_monthly_salary if args.year2_monthly_salary else args.monthly_salary
        annual_bonus = args.year2_annual_bonus if args.year2_annual_bonus else args.annual_bonus
        monthly_social = args.year2_monthly_social_security if args.year2_monthly_social_security else args.monthly_social_security
        monthly_housing = args.year2_monthly_housing_fund if args.year2_monthly_housing_fund else args.monthly_housing_fund
        monthly_deduction = args.year2_monthly_special_deduction if args.year2_monthly_special_deduction else args.monthly_special_deduction
    
    annual_deductions = 60000 + (monthly_social + monthly_housing + monthly_deduction) * 12
    annual_salary = monthly_salary * 12
    
    return {
        'monthly_salary': monthly_salary,
        'annual_salary': annual_salary,
        'annual_deductions': annual_deductions,
        'bonus': annual_bonus,
        'monthly_social': monthly_social,
        'monthly_housing': monthly_housing,
        'monthly_deduction': monthly_deduction
    }

# ==============================================================================
# 结果展示
# ==============================================================================

def get_next_rate(current_rate: str) -> str:
    """获取下一档税率"""
    rates = ["3%", "10%", "20%", "25%", "30%", "35%", "45%"]
    try:
        idx = rates.index(current_rate)
        return rates[idx + 1] if idx + 1 < len(rates) else "45%"
    except:
        return "45%"

def print_bracket_analysis(taxable_income: float, year_label: str, is_optimized: bool = False) -> None:
    """打印工资部分的税率档位分析"""
    bracket = TaxCalculator.get_tax_bracket_info(taxable_income)
    if not bracket:
        return
    
    prefix = "📊" if not is_optimized else "✅"
    print(f"\n  {prefix} 【{year_label} 工资部分税率分析】")
    print(f"     应纳税所得额：¥{bracket['income']:>12,.2f}")
    
    # ✅ 修复：分开处理无穷大的情况
    if bracket['bracket_high'] == float('inf'):
        high_str = "∞"
    else:
        high_str = f"{bracket['bracket_high']:,.0f}"
    
    print(f"     所在税率档：{bracket['bracket_rate']}（区间：{bracket['bracket_low']:,.0f} ~ {high_str} 元）")
    
    if bracket['excess_amount'] > 0 and bracket['bracket_low'] > 0:
        print(f"     🔺 超出档下限：¥{bracket['excess_amount']:>12,.2f}（占本档区间 {bracket['excess_percent']:.1f}%）")
        if bracket['bracket_high'] != float('inf'):
            remaining = bracket['bracket_high'] - bracket['income']
            print(f"     🔻 距上一档：¥{remaining:>12,.2f} 后税率升至 {get_next_rate(bracket['bracket_rate'])}")
    elif bracket['bracket_low'] == 0:
        print(f"     💡 位于最低档 (3%)，还有 ¥{bracket['bracket_high'] - bracket['income']:,.2f} 空间")

def print_input_summary(year1_data: Dict, year2_data: Dict, args: argparse.Namespace) -> None:
    """打印输入数据摘要"""
    print("\n" + "="*85)
    print("📋 输入数据核对")
    print("="*85)
    
    for label, data in [("【第 1 年】", year1_data), ("【第 2 年】", year2_data)]:
        if label == "【第 2 年】" and not (
            args.year2_monthly_salary or args.year2_annual_bonus or 
            args.year2_monthly_social_security or args.year2_monthly_housing_fund or 
            args.year2_monthly_special_deduction
        ):
            print(f"\n{label} (与第 1 年相同，未配置独立参数)")
            continue
        
        print(f"\n{label}")
        print(f"  每月税前工资：        ¥{data['monthly_salary']:>12,.2f}")
        print(f"  预计年终奖金：        ¥{data['bonus']:>12,.2f}")
        print(f"  每月社保 (个人):       ¥{data['monthly_social']:>12,.2f}")
        print(f"  每月公积金 (个人):     ¥{data['monthly_housing']:>12,.2f}")
        print(f"  每月专项附加扣除：    ¥{data['monthly_deduction']:>12,.2f}")
        print(f"  ─────────────────────────────────────────────────────────")
        print(f"  年度工资收入：        ¥{data['annual_salary']:>12,.2f}")
        print(f"  年度扣除总额：        ¥{data['annual_deductions']:>12,.2f}")
    
    print(f"\n📊 【工资部分税率档位预览】(不含任何奖金)")
    for label, data in [("第 1 年", year1_data), ("第 2 年", year2_data)]:
        comp_only = data['annual_salary'] - data['annual_deductions']
        bracket = TaxCalculator.get_tax_bracket_info(comp_only)
        excess_str = f" 🔺超 {bracket['excess_amount']:,.0f} 元" if bracket['excess_amount'] > 0 else ""
        print(f"  {label}：应纳税所得额 ¥{comp_only:>12,.2f} → {bracket['bracket_rate']}档{excess_str}")
    
    print("\n" + "="*85)

def print_optimization_result(result: Dict) -> None:
    """打印优化结果"""
    orig = result['original']
    opt = result['optimized']
    
    print("\n" + "="*85)
    print("📊 原始方案 (奖金全部单独计税，不做任何调整)")
    print("="*85)
    print(f"\n  第 1 年：奖金 ¥{orig['year1_bonus']:>12,.2f}  →  {orig['year1_method']:<20}  →  税额：¥{orig['year1_tax']:>12,.2f}")
    print(f"  第 2 年：奖金 ¥{orig['year2_bonus']:>12,.2f}  →  {orig['year2_method']:<20}  →  税额：¥{orig['year2_tax']:>12,.2f}")
    print(f"  ─────────────────────────────────────────────────────────────────────────────────")
    print(f"  两年总税负：¥{orig['total_tax']:>12,.2f}")
    
    print_bracket_analysis(orig['year1_comp_taxable'], "第 1 年", is_optimized=False)
    print_bracket_analysis(orig['year2_comp_taxable'], "第 2 年", is_optimized=False)
    
    print("\n" + "="*85)
    print("🏆 最优节税方案")
    print("="*85)
    
    if opt['shift_amount'] > 0:
        print(f"\n  💡 建议操作：从第 1 年奖金中递延 ¥{opt['shift_amount']:>12,.2f} 元 到第 2 年发放")
    else:
        print(f"\n  💡 建议操作：无需跨年度递延")
    
    print(f"\n  【第 1 年】奖金总额：¥{opt['year1_bonus_total']:>12,.2f}")
    if opt['year1_bonus_separate'] > 0 and opt['year1_bonus_merged'] > 0:
        print(f"    ├─ 单独计税部分：¥{opt['year1_bonus_separate']:>12,.2f}  (作为年终奖发放)")
        print(f"    └─ 并入工资部分：¥{opt['year1_bonus_merged']:>12,.2f}  (作为绩效工资发放)")
    elif opt['year1_bonus_separate'] > 0:
        print(f"    └─ 全部单独计税：¥{opt['year1_bonus_separate']:>12,.2f}  (作为年终奖发放)")
    else:
        print(f"    └─ 全部并入工资：¥{opt['year1_bonus_merged']:>12,.2f}  (作为绩效工资发放)")
    print(f"    计税方式：{opt['year1_method']}")
    print(f"    预计个税：¥{opt['year1_tax']:>12,.2f}")
    print_bracket_analysis(opt['year1_comp_taxable'], "第 1 年", is_optimized=True)
    
    print(f"\n  【第 2 年】奖金总额：¥{opt['year2_bonus_total']:>12,.2f}")
    if opt['year2_bonus_separate'] > 0 and opt['year2_bonus_merged'] > 0:
        print(f"    ├─ 单独计税部分：¥{opt['year2_bonus_separate']:>12,.2f}  (作为年终奖发放)")
        print(f"    └─ 并入工资部分：¥{opt['year2_bonus_merged']:>12,.2f}  (作为绩效工资发放)")
    elif opt['year2_bonus_separate'] > 0:
        print(f"    └─ 全部单独计税：¥{opt['year2_bonus_separate']:>12,.2f}  (作为年终奖发放)")
    else:
        print(f"    └─ 全部并入工资：¥{opt['year2_bonus_merged']:>12,.2f}  (作为绩效工资发放)")
    print(f"    计税方式：{opt['year2_method']}")
    print(f"    预计个税：¥{opt['year2_tax']:>12,.2f}")
    print_bracket_analysis(opt['year2_comp_taxable'], "第 2 年", is_optimized=True)
    
    print(f"\n  ─────────────────────────────────────────────────────────────────────────────────")
    print(f"  两年总税负：¥{opt['total_tax']:>12,.2f}")
    
    if result['saving'] > 0:
        print(f"\n  🎉 预计节税金额：¥{result['saving']:>12,.2f}")
        print(f"  📈 节税比例：{result['saving']/orig['total_tax']*100:.2f}%")
    else:
        print(f"\n  ℹ️  预计节税金额：¥0.00 (原始方案已最优)")
    
    print("\n" + "="*85)

def print_warnings() -> None:
    """打印注意事项"""
    print("\n⚠️  重要提示：")
    print("  1. 本计算基于现行个税政策（年终奖单独计税优惠延续至 2027 年底）")
    print("  2. 奖金分拆发放需公司财务/HR 配合")
    print("  3. 跨年度递延需公司同意将部分奖金延后至次年发放")
    print("  4. 递延/分拆奖金存在离职无法领取的风险，请谨慎评估")
    print("  5. 社保基数与上年度平均工资挂钩，分拆/递延可能影响明年社保扣款")
    print("  6. 本工具仅供参考，实际纳税以税务局汇算清缴为准")
    print("\n" + "="*85 + "\n")

# ==============================================================================
# 主程序入口
# ==============================================================================

def main():
    """主程序入口"""
    parser = create_argument_parser()
    
    if len(sys.argv) == 1:
        print("\n❌ 错误：缺少必要参数")
        print("💡 示例：python3 tax_optimizer.py --monthly-salary 26200 --annual-bonus 95000 \\")
        print("         --monthly-social-security 2362.5 --monthly-housing-fund 1752 \\")
        print("         --monthly-special-deduction 4500")
        print("📖 使用 --help 查看完整帮助")
        sys.exit(1)
    
    args = parser.parse_args()
    validate_arguments(args)
    
    year1_data = prepare_year_data(args, year=1)
    year2_data = prepare_year_data(args, year=2)
    
    print_input_summary(year1_data, year2_data, args)
    
    engine = OptimizationEngine()
    result = engine.optimize_two_years(year1_data, year2_data)
    
    print_optimization_result(result)
    print_warnings()

if __name__ == "__main__":
    main()