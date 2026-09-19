"""
gantt.py
--------
Renders a Gantt chart in plain text so you can SEE which process ran
during which time interval, directly in the terminal.

A Gantt chart in OS scheduling is a timeline diagram: a horizontal bar
divided into segments, each segment labelled with the process that was
running during that time slice.
"""


def render_gantt_chart(gantt_chart):
    """
    gantt_chart: list of (pid, start_time, end_time) tuples in execution order
    Prints something like:

    |  P1  |    P2    |  P3  |
    0      5          8      16
    """
    if not gantt_chart:
        print("(no processes scheduled)")
        return

    top = "|"
    time_markers = [str(gantt_chart[0][1])]

    for pid, start, end in gantt_chart:
        segment_width = max(len(pid) + 2, len(str(end)) + 1)
        top += f"{pid:^{segment_width}}|"
        time_markers.append(str(end))

    bottom = time_markers[0]
    pos = len(time_markers[0])
    for i, (pid, start, end) in enumerate(gantt_chart):
        segment_width = max(len(pid) + 2, len(str(end)) + 1)
        pos += segment_width + 1
        marker = str(end)
        bottom += marker.rjust(pos - len(bottom))

    print(top)
    print(bottom)