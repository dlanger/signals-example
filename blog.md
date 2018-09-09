For all these examples we'll be using [`signals.py`](https://github.com/dlanger/signals-example), a small Python program that helps us understand which signals have been propagated where. All examples are being run on Ubuntu 18.04 LTS under [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10), and you'll want a few terminal windows open if you're following along. 

### Level I: Your average Python script

Let's see how `signals.py` behaves in the most vanilla of circumstances, before we start adding in more layers. When run directly, `signals.py` starts itself up and waits for input, and from `pstree` we can see that its Python process is a subprocess of the `bash` shell that we're working in.  

```
$ python signals.py
PARENT process PID 55

$ pstree -pgs 55
init(1,1)───init(35,35)───bash(36,36)───python(55,55)
```

`pstree` is a neat little program that visualizes the a process tree. If you give it a PID (here `55`), it'll show you all the processes up and down the tree from it. For every process, you'll see two numbers in brackets following its name - just pay attention to the first one (the PID), which will change from the second one as we get further along.<!--Add endnote about the second one being process group ID--> 

When we send `signals.py` a signal that it knows how to handle - `1` or [`SIGHUP`](http://man7.org/linux/man-pages/man7/signal.7.html) -  it'll display that, and when we send it a signal to gracefully close - `15` or `SIGTERM` - it'll shut down. 

```
$ python signals.py
PARENT process PID 55
==> Caught signal 1 in PID 55
Terminated

$ kill -1 55
$ kill -15 55
```

You'll notice we sent the `SIGTERM` to PID `55` (the Python process), since that's what we're trying to close...and close it did! Now that we have a bit of a handle on what `signals.py` does, let's add some layers.

### Level II: Python with subprocesses

Let's look at those same behaviors, but with a Python script that spawns some subprocesses.

```
$ python signals.py -p
CHILD process (PID 105) of parent PID 104
PARENT process PID 104
CHILD process (PID 106) of parent PID 104

$ pstree -pgs 104
init(1,1)───init(69,69)───bash(70,70)───python(104,104)─┬─python(105,104)
                                                        └─python(106,104)
```

From this (or running it with `-h`), we can see that passing `-p` to `signals.py` causes it to spawn a pair of subprocesses. They're in the same process group as the original script (`104`), but have their own PIDs (`105` and `106`) since they're full-blown processes in their own right. Let's try sending that parent Python process a signal to see if their children get it too: 

```
$ python signals.py -p
CHILD process (PID 105) of parent PID 104
PARENT process PID 104
CHILD process (PID 106) of parent PID 104
==> Caught signal 1 in PID 104

$ kill -1 104
```

It turns out they won't. We see that the signal we sent is only caught in PID `104` (the parent process); if it automatically propagated out to subprocesses, we'd also see that it was caught in PIDs `105` and `106`. This is something to remember, then: **signals aren't automatically propagated to subprocesses**. 

Here's how we can see that. If we stop the parent Python process (`104`), the subprocesses it spawned are still around and need stopping:

```
$ kill -15 104

$ pstree -pgs 104
init(1,1)─┬─python(105,104)
          └─python(106,104)
```

Those orphaned Python subprocesses have been taken over by the `init` process, since that's one of the things it's [responsible for](https://en.wikipedia.org/wiki/Orphan_process). That's fine, so long as you have a real `init` process. We'll come back to that condition in a bit. 

### Level III: Subprocesses and shell scripts

When you're running a web app, it's a common pattern to have a launcher script that does some prep work and then runs your application. This is a reasonable thing to do, but we need to remember signal propagation. Now we have `app-launcher`, a shell script that actually runs `signal.py`. 

```
$ ./app-launcher
Launcher PID is 187
CHILD process (PID 189) of parent PID 188
PARENT process PID 188
CHILD process (PID 190) of parent PID 188

$ pstree -pgs 187
init(1,1)───init(69,69)───bash(70,70)───app-launcher(187,187)───python(188,187)─┬─python(189,187)
                                                                                └─python(190,187)
```

To make sure we're all on the same page, this means that `app-launcher` (PID `187`) spawned the Python subprocess for `signal.py` (PID `188`), which itself spawned two subprocesses (`189` and `190`).

Now, let's say we want to stop that web app, which we started with our launcher script and know is running with PID `187`. We know that signal propagation to subprocesses isn't free, but maybe `bash` - the piping of the Unix world - is a good citizen and does it.

```
$ kill -15 187

$ pstree -pgs 187
init(1,1)───python(188,187)─┬─python(189,187)
                            └─python(190,187)
```

It turns out it isn't. By terminating the launcher script, we haven't done anything to the web app. It's still working fine, but (like before) now has the `init` process as a parent. This hammers home what we learned previously, and has implications for utility and launcher scripts: **when you terminate a `bash` script, the processes it spawned don't get terminated**.

This could be a pain when you're writing utility scripts for things like Jenkins or `supervisord`, but it becomes especially problematic when you're running Docker.

### Level IV: Docker





launchers?

threads?

exec?