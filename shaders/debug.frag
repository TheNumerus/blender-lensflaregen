uniform float aspect_ratio;
uniform vec2 flare_position;

in vec2 uvInterp;

out vec4 FragColor;

void main() {
    vec2 flare_base = (uvInterp - flare_position) * vec2(aspect_ratio, 1.0);

    vec2 cross = max(1.0 - abs(flare_base * 80.0), 0.0);

    FragColor = vec4(cross.yx, 0.0, 1.0);
}
