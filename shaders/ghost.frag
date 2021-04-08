#define E 2.71828
uniform vec4 color;
uniform float empty;

in vec2 posInterp;
in vec4 colorInterp;

out vec4 FragColor;

void main() {
    float center = sqrt(pow(posInterp.x, 2.0) + pow(posInterp.y, 2.0));
    float gauss = 0.4 * pow(E, -(pow(center, 2.0) / 0.3));
    float edge = (1.0 - pow(colorInterp.x, 40.0)) - (gauss * empty);
    FragColor = vec4(color.xyz, edge);
}