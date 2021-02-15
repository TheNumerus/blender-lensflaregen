vertex_shader_ghost = '''
    uniform mat4 modelMatrix;
    uniform mat4 rotationMatrix;
    uniform float aspect_ratio;

    in vec2 position;
    in vec4 vertColor;

    out vec2 posInterp;
    out vec4 colorInterp;

    void main() {
        posInterp = position;
        colorInterp = vertColor;
        vec4 pos_post_rotation = vec4(position, 0.0, 1.0) * rotationMatrix;
        gl_Position = modelMatrix * vec4(pos_post_rotation.xy * vec2(1.0, aspect_ratio), 0.0, 1.0);
    }
'''

vertex_shader_quad = '''
    in vec2 position;
    in vec2 uv;

    out vec2 uvInterp;

    void main() {
        uvInterp = uv;
        gl_Position = vec4(position, 0.0, 1.0);
    }
'''

fragment_shader_ghost = '''
    uniform vec4 color;
    uniform float empty;

    in vec2 posInterp;
    in vec4 colorInterp;

    out vec4 FragColor;

    void main() {
        float center = sqrt(pow(posInterp.x, 2.0) + pow(posInterp.y, 2.0));
        float gauss = 0.4 * pow(2.7, -(pow(center, 2.0) / 0.3));
        float edge = (1.0 - pow(colorInterp.x, 40.0)) - (gauss * empty);
        FragColor = color * edge;
    }
'''

fragment_shader_flare = '''
    uniform vec4 color;
    uniform float size;
    uniform float intensity;
    uniform vec2 flare_position;
    uniform float aspect_ratio;

    in vec2 uvInterp;

    out vec4 FragColor;

    void main() {
        vec2 flare_base = uvInterp - flare_position;
        float dist = sqrt( pow(flare_base.x * aspect_ratio, 2.0) + pow(flare_base.y, 2.0) ); // [0.0; 1.0]
        float flare = max((size/ 100.0) - dist, 0.0) * (100.0 / size);
        FragColor = vec4(flare, flare, flare, 1.0) * color * intensity;
    }
'''