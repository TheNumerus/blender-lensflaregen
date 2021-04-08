uniform mat4 modelMatrix;
uniform mat4 rotationMatrix;
uniform float aspect_ratio;
uniform float ratio;

in vec2 position;
in vec4 vertColor;

out vec2 posInterp;
out vec4 colorInterp;

void main() {
    posInterp = position;
    colorInterp = vertColor;
    vec4 pos_post_rotation = vec4(position, 0.0, 1.0) * rotationMatrix;
    gl_Position = modelMatrix * vec4(pos_post_rotation.xy * vec2(1.0, aspect_ratio) * vec2(1.0 / ratio, 1.0), 0.0, 1.0);
}
