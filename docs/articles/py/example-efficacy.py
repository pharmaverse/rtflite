import pandas as pd
import numpy as np
import rtflite as rtf
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols

np.random.seed(456)

n_subjects = {"Placebo": 100, "Drug 50mg": 101, "Drug 100mg": 99}

efficacy_data = []

for trt, n in n_subjects.items():
    # Treatment effect on change from baseline
    if trt == "Placebo":
        trt_effect = 0
    elif trt == "Drug 50mg":
        trt_effect = -2.5  # Reduction in outcome
    else:  # Drug 100mg
        trt_effect = -4.0  # Greater reduction

    for i in range(n):
        # Baseline characteristics
        age = np.random.normal(55, 10)
        sex = np.random.choice(["M", "F"])
        baseline = np.random.normal(28, 5)  # Baseline score

        # Week 12 outcome with treatment effect
        # Add some correlation with baseline
        week12 = baseline + trt_effect + np.random.normal(0, 3) + 0.3 * (baseline - 28)

        # Week 24 outcome (primary endpoint)
        week24 = (
            baseline + trt_effect * 1.5 + np.random.normal(0, 4) + 0.2 * (baseline - 28)
        )

        efficacy_data.append(
            {
                "USUBJID": f"{trt[:4].upper()}-{i + 1:03d}",
                "TREATMENT": trt,
                "AGE": round(age),
                "SEX": sex,
                "BASELINE": round(baseline, 1),
                "WEEK12": round(week12, 1),
                "WEEK24": round(week24, 1),
                "CHG12": round(week12 - baseline, 1),
                "CHG24": round(week24 - baseline, 1),  # Primary endpoint
            }
        )

df_efficacy = pd.DataFrame(efficacy_data)
print(f"Generated efficacy data for {len(df_efficacy)} subjects")
print(f"\nSample data:\n{df_efficacy.head()}")

summary_stats = []

for trt in ["Placebo", "Drug 50mg", "Drug 100mg"]:
    trt_data = df_efficacy[df_efficacy["TREATMENT"] == trt]

    # Baseline
    baseline_mean = trt_data["BASELINE"].mean()
    baseline_sd = trt_data["BASELINE"].std()

    # Week 24
    week24_mean = trt_data["WEEK24"].mean()
    week24_sd = trt_data["WEEK24"].std()

    # Change from baseline
    chg24_mean = trt_data["CHG24"].mean()
    chg24_sd = trt_data["CHG24"].std()
    chg24_se = chg24_sd / np.sqrt(len(trt_data))

    summary_stats.append(
        {
            "Treatment": trt,
            "N": len(trt_data),
            "Baseline_Mean": baseline_mean,
            "Baseline_SD": baseline_sd,
            "Week24_Mean": week24_mean,
            "Week24_SD": week24_sd,
            "Change_Mean": chg24_mean,
            "Change_SD": chg24_sd,
            "Change_SE": chg24_se,
        }
    )

model = ols("CHG24 ~ TREATMENT + BASELINE", data=df_efficacy).fit()

ls_means = {}
for trt in ["Placebo", "Drug 50mg", "Drug 100mg"]:
    # Create prediction data at mean baseline
    pred_data = pd.DataFrame(
        {"TREATMENT": [trt], "BASELINE": [df_efficacy["BASELINE"].mean()]}
    )
    ls_means[trt] = model.predict(pred_data)[0]

comparisons = []

diff_50_plac = ls_means["Drug 50mg"] - ls_means["Placebo"]
se_50_plac = np.sqrt(
    model.mse_resid * (1 / n_subjects["Drug 50mg"] + 1 / n_subjects["Placebo"])
)
ci_50_plac = stats.t.interval(0.95, model.df_resid, diff_50_plac, se_50_plac)
p_50_plac = model.t_test("TREATMENT[T.Drug 50mg] = 0").pvalue

diff_100_plac = ls_means["Drug 100mg"] - ls_means["Placebo"]
se_100_plac = np.sqrt(
    model.mse_resid * (1 / n_subjects["Drug 100mg"] + 1 / n_subjects["Placebo"])
)
ci_100_plac = stats.t.interval(0.95, model.df_resid, diff_100_plac, se_100_plac)
p_100_plac = model.t_test("TREATMENT[T.Drug 100mg] = 0").pvalue

print(f"\nANCOVA Results:")
print(f"Drug 50mg vs Placebo: Difference = {diff_50_plac:.2f}, p = {p_50_plac:.4f}")
print(f"Drug 100mg vs Placebo: Difference = {diff_100_plac:.2f}, p = {p_100_plac:.4f}")

primary_data = []

for stats in summary_stats:
    primary_data.append(
        [
            stats["Treatment"],
            str(stats["N"]),
            f"{stats['Baseline_Mean']:.1f} ({stats['Baseline_SD']:.2f})",
            f"{stats['Week24_Mean']:.1f} ({stats['Week24_SD']:.2f})",
            f"{stats['Change_Mean']:.1f} ({stats['Change_SE']:.2f})",
            f"{ls_means[stats['Treatment']]:.1f}",
        ]
    )

primary_data.append(["", "", "", "", "", ""])  # Blank row
primary_data.append(["Treatment Comparison", "", "Difference", "95% CI", "p-value", ""])
primary_data.append(
    [
        "Drug 50mg vs Placebo",
        "",
        f"{diff_50_plac:.1f}",
        f"({ci_50_plac[0]:.1f}, {ci_50_plac[1]:.1f})",
        f"{p_50_plac:.4f}",
        "",
    ]
)
primary_data.append(
    [
        "Drug 100mg vs Placebo",
        "",
        f"{diff_100_plac:.1f}",
        f"({ci_100_plac[0]:.1f}, {ci_100_plac[1]:.1f})",
        f"<0.0001",
        "",
    ]
)

df_primary = pd.DataFrame(
    primary_data,
    columns=[
        "Treatment",
        "N",
        "Baseline Mean (SD)",
        "Week 24 Mean (SD)",
        "Change Mean (SE)",
        "LS Mean",
    ],
)

doc = rtf.RTFDocument(
    df=df_primary,
    rtf_page=rtf.RTFPage(orientation="landscape", nrow=40),
    rtf_title=rtf.RTFTitle(
        text=[
            "Table 14.2.1.1: Primary Efficacy Endpoint Analysis",
            "Change from Baseline at Week 24",
            "Full Analysis Set",
        ]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.5, 0.8, 1.8, 1.8, 1.8, 1.3],
        text_justification=["l", "c", "c", "c", "c", "c"],
        border_left=["single"] + [""] * 5,
        border_right=[""] * 5 + ["single"],
        # Bold comparison section headers
        text_format=[
            ["", "", "", "", "", ""],
            ["", "", "", "", "", ""],
            ["", "", "", "", "", ""],
            ["", "", "", "", "", ""],
            ["b", "b", "b", "b", "b", "b"],
            ["", "", "", "", "", ""],
            ["", "", "", "", "", ""],
        ],
        # Add top border for comparison section
        border_top=[
            [""] * 6,
            [""] * 6,
            [""] * 6,
            [""] * 6,
            ["single"] * 6,
            [""] * 6,
            [""] * 6,
        ],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "ANCOVA model: Change = Treatment + Baseline",
            "LS Mean = Least squares mean from ANCOVA model",
            "CI = Confidence interval; N = Number of subjects in Full Analysis Set",
            "p-values < 0.0001 are presented as '<0.0001'",
        ]
    ),
    rtf_source=rtf.RTFSource(text="Source: ADEFF Dataset, Protocol XYZ-2024-001"),
)

doc.write_rtf("../rtf/efficacy_primary.rtf")
print("\nCreated efficacy_primary.rtf")

df_efficacy["RESPONDER"] = df_efficacy["CHG24"] <= -3.0

response_data = []

for trt in ["Placebo", "Drug 50mg", "Drug 100mg"]:
    trt_data = df_efficacy[df_efficacy["TREATMENT"] == trt]
    n_total = len(trt_data)
    n_responders = trt_data["RESPONDER"].sum()
    pct_responders = (n_responders / n_total) * 100

    response_data.append(
        {
            "Treatment": trt,
            "N": n_total,
            "Responders": n_responders,
            "Response_Rate": pct_responders,
        }
    )

from scipy.stats import contingency

placebo_resp = response_data[0]["Responders"]
placebo_nonresp = response_data[0]["N"] - placebo_resp

drug50_resp = response_data[1]["Responders"]
drug50_nonresp = response_data[1]["N"] - drug50_resp

drug100_resp = response_data[2]["Responders"]
drug100_nonresp = response_data[2]["N"] - drug100_resp


def calculate_or_ci(a, b, c, d):
    or_val = (a * d) / (b * c)
    log_or = np.log(or_val)
    se_log_or = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    ci_lower = np.exp(log_or - 1.96 * se_log_or)
    ci_upper = np.exp(log_or + 1.96 * se_log_or)
    return or_val, ci_lower, ci_upper


or_50, ci50_lower, ci50_upper = calculate_or_ci(
    drug50_resp, drug50_nonresp, placebo_resp, placebo_nonresp
)
or_100, ci100_lower, ci100_upper = calculate_or_ci(
    drug100_resp, drug100_nonresp, placebo_resp, placebo_nonresp
)

response_table = []

response_table.append(["Treatment", "n/N", "Response Rate (%)", "Odds Ratio", "95% CI"])

for i, resp in enumerate(response_data):
    if resp["Treatment"] == "Placebo":
        or_text = "Reference"
        ci_text = "-"
    elif resp["Treatment"] == "Drug 50mg":
        or_text = f"{or_50:.2f}"
        ci_text = f"({ci50_lower:.2f}, {ci50_upper:.2f})"
    else:
        or_text = f"{or_100:.2f}"
        ci_text = f"({ci100_lower:.2f}, {ci100_upper:.2f})"

    response_table.append(
        [
            resp["Treatment"],
            f"{resp['Responders']}/{resp['N']}",
            f"{resp['Response_Rate']:.1f}",
            or_text,
            ci_text,
        ]
    )

df_response = pd.DataFrame(response_table[1:], columns=response_table[0])

doc_resp = rtf.RTFDocument(
    df=df_response,
    rtf_page=rtf.RTFPage(orientation="portrait", nrow=40),
    rtf_title=rtf.RTFTitle(
        text=[
            "Table 14.2.2.1: Response Rate Analysis",
            "Proportion of Subjects with ≥3 Point Improvement at Week 24",
            "Full Analysis Set",
        ]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.0, 1.5, 2.0, 1.5, 2.0],
        text_justification=["l", "c", "c", "c", "c"],
        border_left=["single"] + [""] * 4,
        border_right=[""] * 4 + ["single"],
        text_format=["", "", "", "b", ""],  # Bold odds ratios
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Response defined as ≥3 point improvement (reduction) from baseline",
            "Odds Ratio > 1 favors active treatment over placebo",
            "CI = Confidence Interval calculated using Woolf's method",
        ]
    ),
    rtf_source=rtf.RTFSource(
        text=f"Program: t-eff-resp.py | Generated: {pd.Timestamp.now().strftime('%d%b%Y:%H:%M')}"
    ),
)

doc_resp.write_rtf("../rtf/efficacy_response.rtf")
print("Created efficacy_response.rtf")

subgroups = {
    "Overall": lambda df: df,
    "Age < 65": lambda df: df[df["AGE"] < 65],
    "Age ≥ 65": lambda df: df[df["AGE"] >= 65],
    "Male": lambda df: df[df["SEX"] == "M"],
    "Female": lambda df: df[df["SEX"] == "F"],
    "Baseline < Median": lambda df: df[df["BASELINE"] < df["BASELINE"].median()],
    "Baseline ≥ Median": lambda df: df[df["BASELINE"] >= df["BASELINE"].median()],
}

subgroup_results = []

for subgroup_name, filter_func in subgroups.items():
    subgroup_df = filter_func(df_efficacy)

    # Skip if too few subjects
    if len(subgroup_df) < 10:
        continue

    # Calculate means by treatment
    placebo_mean = subgroup_df[subgroup_df["TREATMENT"] == "Placebo"]["CHG24"].mean()
    drug100_mean = subgroup_df[subgroup_df["TREATMENT"] == "Drug 100mg"]["CHG24"].mean()

    # Treatment difference
    diff = drug100_mean - placebo_mean

    # Sample sizes
    n_placebo = len(subgroup_df[subgroup_df["TREATMENT"] == "Placebo"])
    n_drug100 = len(subgroup_df[subgroup_df["TREATMENT"] == "Drug 100mg"])

    subgroup_results.append(
        {
            "Subgroup": subgroup_name,
            "N_Placebo": n_placebo,
            "N_Drug100": n_drug100,
            "Placebo_Mean": placebo_mean,
            "Drug100_Mean": drug100_mean,
            "Difference": diff,
        }
    )

subgroup_table = []
for result in subgroup_results:
    subgroup_table.append(
        [
            result["Subgroup"],
            f"{result['N_Placebo']}",
            f"{result['N_Drug100']}",
            f"{result['Placebo_Mean']:.1f}",
            f"{result['Drug100_Mean']:.1f}",
            f"{result['Difference']:.1f}",
        ]
    )

df_subgroup = pd.DataFrame(
    subgroup_table,
    columns=[
        "Subgroup",
        "N (Placebo)",
        "N (Drug 100mg)",
        "Placebo Mean",
        "Drug 100mg Mean",
        "Difference",
    ],
)


def format_forest_plot(diff):
    # Simple text representation of effect size
    if diff < -7:
        return "◄════════"
    elif diff < -5:
        return "  ◄═════"
    elif diff < -3:
        return "    ◄══"
    else:
        return "     ◄"


df_subgroup["Effect"] = (
    df_subgroup["Difference"].astype(float).apply(format_forest_plot)
)

doc_sub = rtf.RTFDocument(
    df=df_subgroup,
    rtf_page=rtf.RTFPage(orientation="landscape", nrow=40),
    rtf_title=rtf.RTFTitle(
        text=[
            "Table 14.2.3.1: Subgroup Analysis of Primary Endpoint",
            "Change from Baseline at Week 24 - Drug 100mg vs Placebo",
            "Full Analysis Set",
        ]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.5, 1.2, 1.2, 1.5, 1.5, 1.5, 2.0],
        text_justification=["l", "c", "c", "c", "c", "c", "l"],
        text_font=["Times New Roman"] * 6 + ["Courier New"],  # Monospace for plot
        border_left=["single"] + [""] * 6,
        border_right=[""] * 6 + ["single"],
        # Highlight overall row
        text_format=[
            ["b", "b", "b", "b", "b", "b", "b"],
            ["", "", "", "", "", "", ""],
            ["", "", "", "", "", "", ""],
            ["", "", "", "", "", "", ""],
            ["", "", "", "", "", "", ""],
            ["", "", "", "", "", "", ""],
            ["", "", "", "", "", "", ""],
        ],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Difference = Drug 100mg mean - Placebo mean",
            "Negative values favor Drug 100mg (improvement)",
            "Forest plot: ◄ represents magnitude of treatment effect",
        ]
    ),
)

doc_sub.write_rtf("../rtf/efficacy_subgroup.rtf")
print("Created efficacy_subgroup.rtf")
