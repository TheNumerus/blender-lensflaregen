class Shaders:
    @classmethod
    def __read_shader(cls, path: str) -> str:
        import os

        abs_path = os.path.join(os.path.dirname(__file__), path)

        with open(abs_path, 'r') as file:
            return file.read()

    def __init__(self):
        import gpu

        ghost_vs = Shaders.__read_shader('./shaders/ghost.vert')
        quad_vs = Shaders.__read_shader('./shaders/quad.vert')

        ghost_fs = Shaders.__read_shader('./shaders/ghost.frag')
        flare_fs = Shaders.__read_shader('./shaders/flare.frag')
        copy_fs = Shaders.__read_shader('./shaders/dispersion_copy.frag')

        self.ghost = gpu.types.GPUShader(ghost_vs, ghost_fs)
        self.flare = gpu.types.GPUShader(quad_vs, flare_fs)
        self.copy = gpu.types.GPUShader(quad_vs, copy_fs)
