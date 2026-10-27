// SPDX-License-Identifier: GPL-2.0-or-later
// bbport: nearest resample of a depth/stencil image between native and reduced scene
// targets. Used where the format has no blit support (D32S8 on RADV), and for depth-only
// targets with BB_DEPTH_MIN_FILTER=1: a 2x2 min-filter when downscaling (from Mrsuss60's port).

#version 450 core
#extension GL_EXT_samplerless_texture_functions : require
#if defined(HAS_STENCIL) || defined(STENCIL_BITS)
#if defined(HAS_STENCIL)
#extension GL_ARB_shader_stencil_export : require
#endif
layout (binding = 1, set = 0) uniform utexture2D src_stencil;
#endif
#if defined(STENCIL_BITS)
layout (push_constant) uniform StencilBit { uint bit; } pc;
#elif !defined(HAS_STENCIL)
layout (push_constant) uniform ResampleMode { uint downscale; } pc;
#endif

layout (binding = 0, set = 0) uniform texture2D src_depth;

layout (location = 0) in vec2 uv;

void main() {
    const ivec2 size = textureSize(src_depth, 0);
    const ivec2 coord = min(ivec2(uv * vec2(size)), size - 1);
#if defined(STENCIL_BITS)
    // Fixed-function stencil replacement writes one bit per draw. The first draw
    // (bit=0, writeMask=0) copies depth everywhere, including zero-stencil pixels.
    if (pc.bit != 0u && (texelFetch(src_stencil, coord, 0).r & pc.bit) == 0u) discard;
#endif
#if !defined(HAS_STENCIL) && !defined(STENCIL_BITS)
    if (pc.downscale != 0u) {
        // The nearest of the 2x2 source texels under this one (forward Z: the smallest).
        const ivec2 base = clamp(ivec2(floor(uv * vec2(size) - 0.5)), ivec2(0), size - 1);
        const float d0 = texelFetch(src_depth, base, 0).r;
        const float d1 = texelFetch(src_depth, min(base + ivec2(1, 0), size - 1), 0).r;
        const float d2 = texelFetch(src_depth, min(base + ivec2(0, 1), size - 1), 0).r;
        const float d3 = texelFetch(src_depth, min(base + ivec2(1, 1), size - 1), 0).r;
        gl_FragDepth = min(min(d0, d1), min(d2, d3));
        return;
    }
#endif
    gl_FragDepth = texelFetch(src_depth, coord, 0).r;
#if defined(HAS_STENCIL)
    gl_FragStencilRefARB = int(texelFetch(src_stencil, coord, 0).r);
#endif
}
