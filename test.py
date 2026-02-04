import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

np.random.seed(1)

# ========================
# 1️⃣ Charger données Gmail (ou CSV / Excel)
# ========================
# Remplace ceci par le code de lecture Gmail
# df = pd.read_csv("emails_data.csv")
# df = pd.read_excel("emails_data.xlsx")

# Exemple simulé
x = np.linspace(0, 10, 100)
df = pd.DataFrame({
    "date": pd.date_range("2024-01-01", periods=50),
    "emails_received": np.random.randint(5, 50, 50),
    "emails_sent": np.random.randint(1, 30, 50),
    "clicks": np.random.randint(0, 100, 50),
    "open_rate": np.random.rand(50)
})




# ========================
# 2️⃣ Figure 15 graphes
# ========================
fig, axes = plt.subplots(3, 5, figsize=(20, 10))

# 1 Line
axes[0,0].plot(df["date"], df["emails_received"]); axes[0,0].set_title("1. Emails Received")

# 2 Multi-line
axes[0,1].plot(df["date"], df["emails_received"], label="Received")
axes[0,1].plot(df["date"], df["emails_sent"], label="Sent")
axes[0,1].legend(); axes[0,1].set_title("2. Received vs Sent")

# 3 Bar
axes[0,2].bar(df["date"][:10], df["clicks"][:10]); axes[0,2].set_title("3. Clicks Bar")

# 4 Scatter
axes[0,3].scatter(df["emails_received"], df["clicks"]); axes[0,3].set_title("4. Received vs Clicks")

# 5 Bubble
axes[0,4].scatter(df["emails_received"], df["clicks"], s=df["open_rate"]*200); axes[0,4].set_title("5. Bubble (Open Rate)")

# 6 Histogram
axes[1,0].hist(df["emails_received"], bins=10); axes[1,0].set_title("6. Histogram")

# 7 Boxplot
axes[1,1].boxplot([df["emails_received"], df["emails_sent"], df["clicks"]], labels=["Received","Sent","Clicks"]); axes[1,1].set_title("7. Boxplot")

# 8 Area
axes[1,2].fill_between(df["date"], df["emails_received"]); axes[1,2].set_title("8. Area")

# 9 Step
axes[1,3].step(df["date"], df["emails_sent"]); axes[1,3].set_title("9. Step")

# 10 Stem
axes[1,4].stem(df["date"][:20], df["emails_received"][:20]); axes[1,4].set_title("10. Stem")

# 11 Pie
axes[2,0].pie([df["emails_received"].sum(), df["emails_sent"].sum()], labels=["Received","Sent"], autopct="%1.1f%%")
axes[2,0].set_title("11. Pie")

# 12 Heatmap (corrélation)
corr = df[["emails_received","emails_sent","clicks","open_rate"]].corr()
im = axes[2,1].imshow(corr)
axes[2,1].set_title("12. Heatmap")
fig.colorbar(im, ax=axes[2,1])

# 13 Violin
axes[2,2].violinplot(df["emails_received"]); axes[2,2].set_title("13. Violin")

# 14 Log plot
axes[2,3].semilogy(np.arange(len(df)), df["emails_received"]+1); axes[2,3].set_title("14. Log")

# 15 Stackplot
axes[2,4].stackplot(df["date"], df["emails_received"], df["emails_sent"]); axes[2,4].set_title("15. Stackplot")

ax_anim = axes[2,4] 
ax_anim.set_xlim(0, len(df))
ax_anim.set_ylim(0, df["emails_received"].max()+10)
ax_anim.set_title("Animation: Emails Received")
ax_anim.set_xlabel("Date")
ax_anim.set_ylabel("Emails Received")
ax_anim.grid(True)
plt.tight_layout()

# ========================
# 3️⃣ Export PNG / PDF
# ========================
fig.savefig("gmail_dashboard_15_graphs.png", dpi=200)
fig.savefig("gmail_dashboard_15_graphs.pdf")

# ========================
# 4️⃣ Animation simple
# ========================
fig_anim, ax_anim = plt.subplots(figsize=(6,3))
line, = ax_anim.plot([], [], lw=2)
ax_anim.set_xlim(0, len(df))
ax_anim.set_ylim(0, df["emails_received"].max()+10)
ax_anim.set_title("Animation: Emails Received")
ax_anim.set_xlabel("Date")
ax_anim.set_ylabel("Emails Received")
ax_anim.grid(True)


def init():
    line.set_data([], [])
    return line,

def update(frame):
    line.set_data(np.arange(frame), df["emails_received"][:frame])
    return line,

ani = FuncAnimation(fig_anim, update, frames=len(df), init_func=init, blit=True, interval=100)
# Pour sauvegarder animation: ani.save("gmail_animation.mp4", writer="ffmpeg", fps=10)

plt.show()

# ========================
# 5️⃣ Dashboard Tkinter interactif
# ========================
root = tk.Tk()
root.title("Gmail Dashboard 15 Graphs")

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
canvas._tkcanvas.pack(fill=tk.BOTH, expand=1)
tk.mainloop()




