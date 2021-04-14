uniform sampler2D ghost;
uniform sampler2D spectral;
uniform sampler2D noise;
uniform float dispersion;
uniform int samples;
uniform vec3 spectrum_total;
uniform float master_intensity;
uniform float intensity;
uniform vec2 res;
uniform float use_jitter;
uniform float disperse_from_ghost_center;
uniform vec2 ghost_pos;

in vec2 uvInterp;

out vec4 FragColor;

vec2 uv_scaled(vec2 uv, float scale) {
    vec2 centered = uv - 0.5;
    if (disperse_from_ghost_center > 0.5) {
        centered = uv - ghost_pos / 2.0 - 0.5;
    }
    vec2 scaled = centered * scale;
    if (disperse_from_ghost_center > 0.5) {
        return scaled + ghost_pos / 2.0 + 0.5;
    }
    return scaled + 0.5;
}

void main() {
    if (abs(dispersion) < 0.001) {
        // use precalculated spetrum integral for total brightness
        FragColor = vec4(texture(ghost, uvInterp).rgb * spectrum_total * intensity * master_intensity, 1.0);
        return;
    }

    vec3 color = vec3(0.0);
    for (int i = 0; i < samples; ++i) {
        float x = (float(i) + texture(noise, uvInterp * res).r * use_jitter) / float(samples);
        vec4 spectral_tex = texture(spectral, vec2(x, x));

        float sample_dispersion = (x - 0.5) * 2.0 * (dispersion) + 1.0;

        vec4 ghost_color = texture(ghost, uv_scaled(uvInterp, sample_dispersion));

        color += ghost_color.rgb * spectral_tex.rgb;
    }

    color /= float(samples);

    FragColor = vec4(color * intensity * master_intensity, 1.0);
}