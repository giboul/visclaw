import sys
from pathlib import Path
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from clawpack.visclaw.frametools import call_setplot, plotframe
from clawpack.visclaw.data import ClawPlotData


class Iplot:

    def __init__(self, setplot=None, outdir=None, plotdir=None):
        """Take advantage of `setplot` and `plotframe` to make an interactive plotting session."""
        self.plotdata = ClawPlotData()
        self.plotdata._mode = 'iplotclaw'

        if outdir is None and Path(".outdir").is_file():
            with open(".outdir", "r") as file:
                outdir = file.readline().strip()
        self.plotdata.outdir = outdir or "_output"
        self.plotdata.setplot = setplot or "setplot.py"
        self.plotdata = call_setplot(setplot, self.plotdata)
        self.plotdir = plotdir or "_plots"

        self.settings = dict(current=0, max=0, right=1, left=-1, up=1, down=-1)
        self.settings["max"] = len(list(Path(self.plotdata.outdir).glob("fort.q*")))
        self.settings["fignotxt"] = ""
        self.settings["title"] = "Use ←/→ or input a frame index and press enter.%s"
        self.update(0)

        for fn in plt.get_fignums():
            plt.figure(fn).canvas.mpl_connect('key_press_event', self.arrow_key)
            plt.figure(fn).canvas.mpl_connect('key_press_event', self.to_frame)
            plt.figure(fn).canvas.mpl_connect('key_press_event', self.save_all)
            plt.figure(fn).canvas.mpl_connect('key_press_event', self.write)
            plt.figure(fn).canvas.manager.set_window_title(self.settings["title"] % "")

    def animate(self, fps):
        return FuncAnimation(plt.gcf(), self.update, frames=self.settings["max"], interval=1e3/fps)

    def write(self, event=None, fps=2, fname="movie.gif"):
        if event.key == "w" or event is None:
            anim = self.animate(fps)
            anim.save(fname)

    def update(self, i):
        plotframe(i, self.plotdata, simple=False, refresh=True)

    def arrow_key(self, event):
        """If pressed key is in settings, increment index and update plot."""
        if event.key in self.settings:
            prev = self.settings["current"]
            self.settings["current"] += self.settings[event.key]
            self.settings["current"] = max(0, min(self.settings["max"]-1, self.settings["current"]))
            if prev != self.settings["current"]:
                self.update(self.settings["current"])

    def to_frame(self, event):
        if event.key.isnumeric():
            self.settings["fignotxt"] += event.key
            for fn in plt.get_fignums():
                if plt.fignum_exists(fn):
                    plt.figure(fn).canvas.manager.set_window_title(
                        self.settings["title"] % f" (#{self.settings['fignotxt']})"
                    )
        elif event.key == "enter":
            prev = self.settings["current"]
            self.settings["current"] = int(self.settings["fignotxt"] or 0)
            self.settings["current"] = max(0, min(self.settings["max"]-1, self.settings["current"]))
            self.settings["fignotxt"] = ""
            if prev != self.settings["current"]:
                self.update(self.settings["current"])
            for fn in plt.get_fignums():
                if plt.fignum_exists(fn):
                    plt.figure(fn).canvas.manager.set_window_title(
                        self.settings["title"] % f""
                    )

    def save_all(self, event):
        if event.key == "a":
            plotdir = Path(self.plotdir)
            plotdir.mkdir(exist_ok=True)
            nsols = self.settings["max"]
            s_digits = len(str(nsols))
            fignums = plt.get_fignums()
            f_digits = len(fignums)
            for i in range(nsols):
                self.update(i)
                for fn in fignums:
                    if plt.fignum_exists(fn):
                        fignum = f"fig{fn:0>{f_digits}}"
                        solnum = f"sol{i:0>{s_digits}}"
                        f = plotdir / f"{fignum}_{solnum}.png"
                        plt.savefig(f)


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("outdir", default="./_output", type=str, nargs="?")
    parser.add_argument("setplot", default="setplot.py", type=str, nargs="?")
    parser.add_argument("plotdir", default="_plots", type=str, nargs="?")
    parser.add_argument("--fname", default=None, type=str, required=False)
    parser.add_argument("--fps", default=None, type=float, required=False)
    args = parser.parse_args()
    iplot = Iplot(args.setplot, args.outdir)

    if args.fname and args.fps:
        if not args.fps:
            raise ValueError("Pleave provide both `fname` and `fps`")
        iplot.write(fps=args.fps, fname=args.fname)
        return None

    if args.fps:
        anim = iplot.animate(args.fps)

    plt.show(block=True)


if __name__ == "__main__":
    main()
