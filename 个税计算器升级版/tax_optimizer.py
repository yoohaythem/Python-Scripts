# -*- coding: utf-8 -*-
"""
全国通用 - 年终一次性奖金多年最优提取计算工具 (CLI 命令行版)
作者：于海翔
版本：2026.3

功能：
    1. 计算年终奖单独计税 vs 并入综合所得的最优方案
    2. 支持1-2年联动优化（奖金递延/提前），寻找全局最低税负
    3. 内置 2026 年最新个税专项附加扣除标准

================================================================================
快速使用示例：
================================================================================

# 场景 1：基础计算（两年收入相同）
python tax_optimizer.py --monthly-salary 15000 --annual-bonus 80000 --monthly-social-security 2000 --monthly-housing-fund 2000 --monthly-special-deduction 4500 --optimization-years 1
python tax_optimizer.py --monthly-salary 15000 --annual-bonus 80000 --monthly-social-security 2000 --monthly-housing-fund 2000 --monthly-special-deduction 4500 --optimization-years 2

# 场景 2：明年收入有变化（如涨薪、奖金变化）
python tax_optimizer.py --monthly-salary 25000 --annual-bonus 80000 --monthly-social-security 2000 --monthly-housing-fund 2000 --monthly-special-deduction 4500 --year2-annual-bonus 100000 --optimization-years 2

# 场景 3：查看完整帮助和扣除标准说明
python tax_optimizer.py --help

================================================================================
"""

import argparse
import sys
from typing import Dict, Tuple, List

# ==============================================================================
# 税率表配置
# ==============================================================================

class TaxRates:
    """个税税率表配置"""
    
    COMPREHENSIVE_RATES = [
        (0, 36000, 0.03, 0, "3%"),
        (36000, 144000, 0.10, 2520, "10%"),
        (144000, 300000, 0.20, 16920, "20%"),
        (300000, 420000, 0.25, 31920, "25%"),
        (420000, 660000, 0.30, 52920, "30%"),
        (660000, 960000, 0.35, 85920, "35%"),
        (960000, float('inf'), 0.45, 181920, "45%")
    ]
    
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
                percent = excess / (high - low) * 100 if high != float('inf') else 0
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
    """多年奖金优化引擎（支持 1-2 年优化）"""
    
    def __init__(self, years: int = 2):
        self.calculator = TaxCalculator()
        self.years = years
    
    def optimize_multi_years(self, years_data: List[Dict]) -> Dict:
        """执行多年联动优化"""
        
        n = len(years_data)
        
        # 提取基础数据
        salaries = [d['annual_salary'] for d in years_data]
        deductions = [d['annual_deductions'] for d in years_data]
        bonuses = [d['bonus'] for d in years_data]
        socials = [d['monthly_social'] * 12 for d in years_data]
        housings = [d['monthly_housing'] * 12 for d in years_data]
        
        total_bonus_pool = sum(bonuses)
        
        print(f"🔍 正在搜索最优方案...（{n} 年奖金池总计 {total_bonus_pool:,.0f} 元）")
        
        if n == 1:
            return self._optimize_single_year(salaries[0], deductions[0], bonuses[0], 
                                              socials[0], housings[0])
        elif n == 2:
            return self._optimize_two_years(salaries, deductions, bonuses, socials, housings)
        else:
            raise ValueError("目前仅支持 1-2 年优化")
    
    def _optimize_single_year(self, salary: float, deduction: float, bonus: float, 
                              social: float, housing: float) -> Dict:
        """单年优化"""
        best_config = {}
        min_tax = float('inf')
        split_step = 1000
        
        for split in range(0, int(bonus) + 1, split_step):
            tax, method, comp = self.calculator.calculate_year_tax_with_split(
                salary, deduction, bonus, split
            )
            if tax < min_tax:
                min_tax = tax
                best_config = {
                    'year1_bonus_total': bonus,
                    'year1_bonus_separate': split,
                    'year1_bonus_merged': bonus - split,
                    'year1_tax': tax,
                    'year1_method': method,
                    'year1_comp_taxable': comp,
                    'total_tax': tax
                }
        
        orig_tax, orig_method, orig_comp = self.calculator.calculate_year_tax_with_split(
            salary, deduction, bonus, bonus
        )
        
        return {
            'years': 1,
            'original': {
                'year1_tax': orig_tax,
                'year1_method': orig_method,
                'year1_bonus': bonus,
                'year1_comp_taxable': orig_comp,
                'total_tax': orig_tax
            },
            'optimized': best_config,
            'saving': orig_tax - min_tax,
            'social': social,
            'housing': housing
        }
    
    def _optimize_two_years(self, salaries: List, deductions: List, bonuses: List,
                           socials: List, housings: List) -> Dict:
        """两年优化"""
        s1, s2 = salaries[0], salaries[1]
        d1, d2 = deductions[0], deductions[1]
        b1, b2 = bonuses[0], bonuses[1]
        
        orig_tax1, orig_method1, orig_comp1 = self.calculator.calculate_year_tax_with_split(s1, d1, b1, b1)
        orig_tax2, orig_method2, orig_comp2 = self.calculator.calculate_year_tax_with_split(s2, d2, b2, b2)
        orig_total_tax = orig_tax1 + orig_tax2
        
        best_config = {}
        min_total_tax = float('inf')
        shift_step = 1000
        split_step = 1000
        
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
            'years': 2,
            'original': {
                'year1_tax': orig_tax1, 'year1_method': orig_method1, 'year1_bonus': b1,
                'year1_comp_taxable': orig_comp1,
                'year2_tax': orig_tax2, 'year2_method': orig_method2, 'year2_bonus': b2,
                'year2_comp_taxable': orig_comp2,
                'total_tax': orig_total_tax
            },
            'optimized': best_config,
            'saving': orig_total_tax - min_total_tax,
            'socials': socials,
            'housings': housings
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
💡 专项附加扣除标准参考 (2024 年最新版)
================================================================================

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

⚠️ 注意事项：
   1. 住房租金和住房贷款利息只能二选一
   2. 本工具基于现行个税政策（年终奖单独计税优惠延续至 2027 年底）
   3. 奖金分拆发放需公司财务/HR 配合
   4. 社保基数与上年度平均工资挂钩，分拆/递延可能影响明年社保扣款

================================================================================
        ''',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('--optimization-years', type=int, default=2, choices=[1, 2],
        help='优化年限：1=单年，2=两年联动 (默认)')
    
    year1_group = parser.add_argument_group('📅 第 1 年收入参数 (必填)')
    year1_group.add_argument('--monthly-salary', type=float, required=True, metavar='金额',
        help='第 1 年每月税前工资 (元)')
    year1_group.add_argument('--annual-bonus', type=float, required=True, metavar='金额',
        help='第 1 年预计年终奖金总额 (元)')
    year1_group.add_argument('--monthly-social-security', type=float, required=True, metavar='金额',
        help='第 1 年每月社保个人缴纳 (元)')
    year1_group.add_argument('--monthly-housing-fund', type=float, required=True, metavar='金额',
        help='第 1 年每月公积金个人缴纳 (元)')
    year1_group.add_argument('--monthly-special-deduction', type=float, required=True, metavar='金额',
        help='第 1 年每月专项附加扣除总额 (元)')
    
    year2_group = parser.add_argument_group('📅 第 2 年收入参数 (选填)')
    year2_group.add_argument('--year2-monthly-salary', type=float, default=None, metavar='金额')
    year2_group.add_argument('--year2-annual-bonus', type=float, default=None, metavar='金额')
    year2_group.add_argument('--year2-monthly-social-security', type=float, default=None, metavar='金额')
    year2_group.add_argument('--year2-monthly-housing-fund', type=float, default=None, metavar='金额')
    year2_group.add_argument('--year2-monthly-special-deduction', type=float, default=None, metavar='金额')
    
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
    # argparse 将 - 转换为 _，所以这里要用下划线
    prefixes = {
        1: ('', '', '', '', ''),
        2: ('year2_', 'year2_', 'year2_', 'year2_', 'year2_')
    }
    
    p = prefixes.get(year, prefixes[1])
    
    # 获取值，如果当年没传则用第 1 年的值
    monthly_salary = getattr(args, f"{p[0]}monthly_salary") if getattr(args, f"{p[0]}monthly_salary", None) else args.monthly_salary
    annual_bonus = getattr(args, f"{p[1]}annual_bonus") if getattr(args, f"{p[1]}annual_bonus", None) else args.annual_bonus
    monthly_social = getattr(args, f"{p[2]}monthly_social_security") if getattr(args, f"{p[2]}monthly_social_security", None) else args.monthly_social_security
    monthly_housing = getattr(args, f"{p[3]}monthly_housing_fund") if getattr(args, f"{p[3]}monthly_housing_fund", None) else args.monthly_housing_fund
    monthly_deduction = getattr(args, f"{p[4]}monthly_special_deduction") if getattr(args, f"{p[4]}monthly_special_deduction", None) else args.monthly_special_deduction
    
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

def print_input_summary(years_data: List[Dict], args: argparse.Namespace) -> None:
    """打印输入数据摘要"""
    print("\n" + "="*90)
    print("📋 输入数据核对")
    print("="*90)
    
    for i, data in enumerate(years_data):
        year_label = f"【第 {i+1} 年】"
        print(f"\n{year_label}")
        print(f"  每月税前工资：        ¥{data['monthly_salary']:>12,.2f}")
        print(f"  预计年终奖金：        ¥{data['bonus']:>12,.2f}")
        print(f"  每月社保 (个人):       ¥{data['monthly_social']:>12,.2f}")
        print(f"  每月公积金 (个人):     ¥{data['monthly_housing']:>12,.2f}")
        print(f"  每月专项附加扣除：    ¥{data['monthly_deduction']:>12,.2f}")
        print(f"  ─────────────────────────────────────────────────────────")
        print(f"  年度工资收入：        ¥{data['annual_salary']:>12,.2f}")
        print(f"  年度扣除总额：        ¥{data['annual_deductions']:>12,.2f}")
    
    print(f"\n📊 【工资部分税率档位预览】(不含任何奖金)")
    for i, data in enumerate(years_data):
        comp_only = data['annual_salary'] - data['annual_deductions']
        bracket = TaxCalculator.get_tax_bracket_info(comp_only)
        excess_str = f" 🔺超 {bracket['excess_amount']:,.0f} 元" if bracket['excess_amount'] > 0 else ""
        print(f"  第{i+1}年：应纳税所得额 ¥{comp_only:>12,.2f} → {bracket['bracket_rate']}档{excess_str}")
    
    print("\n" + "="*90)

def print_income_summary(years_data: List[Dict], result: Dict) -> None:
    """打印收入汇总（税前 vs 税后）"""
    n = result['years']
    opt = result['optimized']
    
    print("\n" + "="*90)
    print("💰 收入汇总（税前 vs 税后到手）")
    print("="*90)
    
    total_gross = 0
    total_social = 0
    total_housing = 0
    total_tax = 0
    total_net = 0
    
    print(f"\n{'年度':<8} {'税前工资':>14} {'税前奖金':>14} {'社保':>12} {'公积金':>12} {'个税':>12} {'税后到手':>14}")
    print(f"{'─'*90}")
    
    for i in range(n):
        year_key = f"year{i+1}"
        data = years_data[i]
        
        gross_salary = data['annual_salary']
        gross_bonus = opt[f'{year_key}_bonus_total']
        social = data['monthly_social'] * 12
        housing = data['monthly_housing'] * 12
        tax = opt[f'{year_key}_tax']
        net = gross_salary + gross_bonus - social - housing - tax
        
        total_gross += gross_salary + gross_bonus
        total_social += social
        total_housing += housing
        total_tax += tax
        total_net += net
        
        print(f"第{i+1}年   ¥{gross_salary:>12,.2f}   ¥{gross_bonus:>12,.2f}   ¥{social:>10,.2f}   ¥{housing:>10,.2f}   ¥{tax:>10,.2f}   ¥{net:>12,.2f}")
    
    print(f"{'─'*90}")
    print(f"合计     ¥{total_gross:>12,.2f}   {'':>12}   ¥{total_social:>10,.2f}   ¥{total_housing:>10,.2f}   ¥{total_tax:>10,.2f}   ¥{total_net:>12,.2f}")
    
    print(f"\n📈 收入分析：")
    print(f"  税前总收入：    ¥{total_gross:>12,.2f}")
    print(f"  社保总扣除：    ¥{total_social:>12,.2f}  ({total_social/total_gross*100:.1f}%)")
    print(f"  公积金总扣除：  ¥{total_housing:>12,.2f}  ({total_housing/total_gross*100:.1f}%)")
    print(f"  个税总缴纳：    ¥{total_tax:>12,.2f}  ({total_tax/total_gross*100:.1f}%)")
    print(f"  ─────────────────────────────────")
    print(f"  税后到手收入：  ¥{total_net:>12,.2f}")
    print(f"  综合税负率：    {total_tax/total_gross*100:.2f}%")
    
    print("\n" + "="*90)

def print_optimization_result(result: Dict, years_data: List[Dict]) -> None:
    """打印优化结果"""
    n = result['years']
    orig = result['original']
    opt = result['optimized']
    
    print("\n" + "="*90)
    print("📊 原始方案 (奖金全部单独计税，不做任何调整)")
    print("="*90)
    
    for i in range(n):
        year_key = f"year{i+1}"
        print(f"  第{i+1}年：奖金 ¥{orig[f'{year_key}_bonus']:>12,.2f}  →  {orig[f'{year_key}_method']:<20}  →  税额：¥{orig[f'{year_key}_tax']:>12,.2f}")
    print(f"  ─────────────────────────────────────────────────────────────────────────────────")
    print(f"  总税负：¥{orig['total_tax']:>12,.2f}")
    
    for i in range(n):
        year_key = f"year{i+1}"
        print_bracket_analysis(orig[f'{year_key}_comp_taxable'], f"第{i+1}年", is_optimized=False)
    
    print("\n" + "="*90)
    print("🏆 最优节税方案")
    print("="*90)
    
    if n == 2 and opt.get('shift_amount', 0) > 0:
        print(f"\n  💡 建议操作：从第 1 年奖金中递延 ¥{opt['shift_amount']:>12,.2f} 元 到第 2 年发放")
    else:
        print(f"\n  💡 建议操作：无需跨年度递延")
    
    for i in range(n):
        year_key = f"year{i+1}"
        print(f"\n  【第{i+1}年】奖金总额：¥{opt[f'{year_key}_bonus_total']:>12,.2f}")
        
        separate = opt[f'{year_key}_bonus_separate']
        merged = opt[f'{year_key}_bonus_merged']
        
        if separate > 0 and merged > 0:
            print(f"    ├─ 单独计税部分：¥{separate:>12,.2f}  (作为年终奖发放)")
            print(f"    └─ 并入工资部分：¥{merged:>12,.2f}  (作为绩效工资发放)")
        elif separate > 0:
            print(f"    └─ 全部单独计税：¥{separate:>12,.2f}  (作为年终奖发放)")
        else:
            print(f"    └─ 全部并入工资：¥{merged:>12,.2f}  (作为绩效工资发放)")
        
        print(f"    计税方式：{opt[f'{year_key}_method']}")
        print(f"    预计个税：¥{opt[f'{year_key}_tax']:>12,.2f}")
        print_bracket_analysis(opt[f'{year_key}_comp_taxable'], f"第{i+1}年", is_optimized=True)
    
    print(f"\n  ─────────────────────────────────────────────────────────────────────────────────")
    print(f"  总税负：¥{opt['total_tax']:>12,.2f}")
    
    if result['saving'] > 0:
        print(f"\n  🎉 预计节税金额：¥{result['saving']:>12,.2f}")
        print(f"  📈 节税比例：{result['saving']/orig['total_tax']*100:.2f}%")
    else:
        print(f"\n  ℹ️  预计节税金额：¥0.00 (原始方案已最优)")
    
    print("\n" + "="*90)

def print_warnings() -> None:
    """打印注意事项"""
    print("\n⚠️  重要提示：")
    print("  1. 本计算基于现行个税政策（年终奖单独计税优惠延续至 2027 年底）")
    print("  2. 社保基数与上年度平均工资挂钩，分拆/递延可能影响明年社保扣款")
    print("  3. 本工具仅供参考，实际纳税以税务局汇算清缴为准")
    print("\n" + "="*90 + "\n")

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
        print("         --monthly-special-deduction 4500 --optimization-years 2")
        print("📖 使用 --help 查看完整帮助")
        sys.exit(1)
    
    args = parser.parse_args()
    validate_arguments(args)
    
    years_data = []
    for i in range(1, args.optimization_years + 1):
        years_data.append(prepare_year_data(args, year=i))
    
    print_input_summary(years_data, args)
    
    engine = OptimizationEngine(years=args.optimization_years)
    result = engine.optimize_multi_years(years_data)
    
    print_optimization_result(result, years_data)
    print_income_summary(years_data, result)
    print_warnings()
    
if __name__ == "__main__":

    main()

