## Install mesalib
DMC environments require the mesalib library to function correctly. We recommend to create a virtual environment with [Anaconda](https://anaconda.org/) or [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/)  and run the following commands:

```bash
conda create -n myenv python=3.10
conda activate myenv
conda install -c conda-forge mesalib
```

## Install Gymnasium MuJoCo/DMC environments
Now, you should install the proper environments:

- MuJoCo (Gymnasium): you do not need to install extra pakages, the `pip install -e .` command is enough to have available all the MuJoCo environments provided by Gymnasium (https://gymnasium.farama.org/environments/mujoco/)
- DMC: you have to install extra packages with the following command: `pip install -e .[dmc]`. (https://github.com/deepmind/dm_control).

## Install OpenGL rendering backands packages

MuJoCo/DMC supports three different OpenGL rendering backends: EGL (headless), GLFW (windowed), OSMesa (headless).
For each of them, you need to install some pakages:
- GLFW: `sudo apt-get install libglfw3 libglew2.0`
- EGL: `sudo apt-get install libglew2.0`
- OSMesa: `sudo apt-get install libgl1-mesa-glx libosmesa6`
In order to use one of these rendering backends, you need to set the `MUJOCO_GL` environment variable to `"glfw"`, `"egl"`, `"osmesa"`, respectively.

For more information: [https://github.com/deepmind/dm_control](https://github.com/deepmind/dm_control) and [https://mujoco.readthedocs.io/en/stable/programming/index.html#using-opengl](https://mujoco.readthedocs.io/en/stable/programming/index.html#using-opengl)

## MuJoCo Gymnasium
In order to train your agents on the [MuJoCo environments](https://gymnasium.farama.org/environments/mujoco/) provided by Gymnasium, it is sufficient to select the *GYM* environment (`env=gym`) and set the `env.id` to the name of the environment you want to use. For instance, `"Walker2d-v4"` if you want to train your agent on the *walker walk* environment.

```bash
lightning run model sheeprl.py dreamer_v3 exp=dreamer_v3 env=gym env.id=Walker2d-v4 cnn_keys.encoder=[rgb]
```

## DeepMind Control
In order to train your agents on the [DeepMind control suite](https://github.com/deepmind/dm_control/blob/main/dm_control/suite/README.md), you have to select the *DMC* environment (`env=dmc`) and to set the id of the environment you want to use. A list of the available environments can be found [here](https://arxiv.org/abs/1801.00690). For instance, if you want to train your agent on the *walker walk* environment, you need to set the `env.id` to `"walker_walk"`.

```bash
lightning run model sheeprl.py dreamer_v3 exp=dreamer_v3 env=dmc env.id=walker_walk cnn_keys.encoder=[rgb]
```