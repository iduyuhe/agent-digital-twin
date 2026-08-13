import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

dims = ["几何保真", "仿真保真", "数据保真", "智能保真", "可信性"]
v140 = [70, 95, 80, 95, 100]   # v1.4.0 baseline
v150 = [70, 95, 90, 95, 100]   # v1.5.0 (A2 done)
va1  = [85, 95, 90, 95, 100]   # A1 OCCT enabled (current)
x = np.arange(len(dims))
w = 0.28

fig, ax = plt.subplots(figsize=(10, 5.2))
b1 = ax.bar(x - w, v140, w, label="v1.4.0 (综合 88 · L3)", color="#94a3b8")
b2 = ax.bar(x,     v150, w, label="v1.5.0 (综合 90 · L4)", color="#60a5fa")
b3 = ax.bar(x + w, va1,  w, label="A1 收口 (综合 93 · L4)", color="#2563eb")

# L4 threshold line
ax.axhline(90, color="#f59e0b", linestyle="--", linewidth=1.6)
ax.text(len(dims)-0.5, 90.4, "L4 threshold >=90", color="#f59e0b",
        fontsize=10, ha="right", fontweight="bold")

ax.set_ylim(0, 110)
ax.set_ylabel("Maturity Score", fontsize=11)
ax.set_title("CESI Trustworthiness Maturity: v1.4.0 -> v1.5.0 -> A1 (OCCT) Dimension Lift", fontsize=13, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(dims, fontsize=10)
ax.set_yticks(range(0, 111, 10))
ax.legend(loc="lower right", fontsize=9)
ax.grid(axis="y", linestyle=":", alpha=0.5)

# value labels
for b in (b1, b2, b3):
    for rect in b:
        h = rect.get_height()
        ax.annotate(f"{int(h)}", xy=(rect.get_x()+rect.get_width()/2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", fontsize=8.5)

# top summary badge
ax.text(0.5, 1.02, "Overall  88 -> 90 -> 93  (L4 achieved, OCCT geometry kernel enabled)",
        transform=ax.transAxes,
        ha="center", fontsize=12, fontweight="bold", color="#2563eb")
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig("docs/assets/demo_maturity_v1.5.0.png", dpi=140)
print("saved docs/assets/demo_maturity_v1.5.0.png")
