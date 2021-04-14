uniform vec4 color;
uniform float empty;

in vec2 posInterp;
in vec4 colorInterp;

out vec4 FragColor;

void main() {
    float center = sqrt(pow(posInterp.x, 2.0) + pow(posInterp.y, 2.0));
    float edge;
    if (empty < 1.0) {
        edge = (1.0 - pow(colorInterp.x, 40.0) - (gauss(center, 0.0, 0.3)) * empty);
    } else {
        edge = (1.0 - pow(colorInterp.x, 40.0) - (gauss(pow(center, empty), 0.0, 0.3)));
    }
    FragColor = vec4(color.xyz, edge);
}