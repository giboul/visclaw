import sys
from pathlib import Path
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from clawpack.visclaw.frametools import call_setplot, plotframe
from clawpack.visclaw.data import ClawPlotData


def interactive_plot(setplot=None, outdir=None, fps=None):
    """Take advantage of Iplotclaw to make an interactive plotting session."""
    plotdata = ClawPlotData()
    plotdata._mode = 'iplotclaw'

    plotdata.setplot = setplot or "setplot.py"
    plotdata.outdir = outdir or "_output"
    if outdir is None and Path(".outdir").is_file():
        with open(".outdir", "r") as file:
            outdir = file.readline().strip()
    plotdata = call_setplot(setplot, plotdata)

    settings = dict(current=0, max=0, right=1, left=-1, up=1, down=-1)
    settings["max"] = len(list(Path(plotdata.outdir).glob("fort.q*")))
    settings["fignotxt"] = ""
    settings["title"] = "Use ←/→ or input a frame index and press enter.%s"

    def update(i):
        plotframe(i, plotdata, simple=False, refresh=True)
    update(0)

    def arrow_key(event):
        """If pressed key is in settings, increment index and update plot."""
        if event.key in settings:
            prev = settings["current"]
            settings["current"] += settings[event.key]
            settings["current"] = max(0, min(settings["max"]-1, settings["current"]))
            if prev != settings["current"]:
                update(settings["current"])

    def to_frame(event):
        if event.key.isnumeric():
            settings["fignotxt"] += event.key
            for fn in plt.get_fignums():
                if plt.fignum_exists(fn):
                    plt.figure(fn).canvas.manager.set_window_title(
                        settings["title"] % f" (#{settings["fignotxt"]})"
                    )
        elif event.key == "enter":
            prev = settings["current"]
            settings["current"] = int(settings["fignotxt"] or 0)
            settings["current"] = max(0, min(settings["max"]-1, settings["current"]))
            settings["fignotxt"] = ""
            if prev != settings["current"]:
                update(settings["current"])
            for fn in plt.get_fignums():
                if plt.fignum_exists(fn):
                    plt.figure(fn).canvas.manager.set_window_title(
                        settings["title"] % f""
                    )
    
    def save_all(event):
        """Save all frames."""
        if event.key == "a":
            raise NotImplementedError()

    for fn in plt.get_fignums():
        plt.figure(fn).canvas.mpl_connect('key_press_event', arrow_key)
        plt.figure(fn).canvas.mpl_connect('key_press_event', to_frame)
        plt.figure(fn).canvas.manager.set_window_title(settings["title"] % "")

    if fps:
        return FuncAnimation(plt.gcf(), update, frames=settings["max"], interval=1e3/fps)

def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("outdir", default="./_output", type=str, nargs="?")
    parser.add_argument("setplot", default="setplot.py", type=str, nargs="?")
    parser.add_argument("--fname", default=None, type=str, required=False)
    parser.add_argument("--fps", default=None, type=float, required=False)
    args = parser.parse_args()
    anim = interactive_plot(args.setplot, args.outdir, args.fps)

    if args.fname:
        if not args.fps:
            raise ValueError(f"Please provide a value for `fps=...`")
        fname = args.fname or "movie.gif"
        anim.save(fname)
    else:
        plt.show(block=True)


if __name__ == "__main__":
    main()
