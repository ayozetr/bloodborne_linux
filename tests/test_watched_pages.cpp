// SPDX-License-Identifier: GPL-2.0-or-later
// The texture cache's watched page counts (watched_pages.h), as the write fault path reads them.
#include <cassert>
#include <cstdio>
#include <memory>
#include "video_core/texture_cache/watched_pages.h"

int main() {
    auto pages = std::make_unique<VideoCore::WatchedPages>();
    // Nothing watched: a fault anywhere skips the texture cache.
    assert(!pages->Any(0x100000, 8));
    // An image over [0x10800, 0x13010): pages 0x10..0x13 watched, the pages beside them not.
    pages->Add(0x10800, 0x2810, 1);
    assert(pages->Any(0x10000, 8) && pages->Any(0x13008, 8) && pages->Any(0x12ff8, 0x10));
    assert(!pages->Any(0xf000, 0x1000) && !pages->Any(0x14000, 8));
    // A second image over one of those pages; the first untracked: that page stays watched.
    pages->Add(0x12000, 0x1000, 1);
    pages->Add(0x10800, 0x2810, -1);
    assert(pages->Any(0x12abc, 4) && !pages->Any(0x10000, 0x2000) && !pages->Any(0x13000, 8));
    pages->Add(0x12000, 0x1000, -1);
    assert(!pages->Any(0x10000, 0x4000));
    // An untrack never seen as a track (a chunk never allocated) is ignored; a count never
    // goes below zero.
    pages->Add(0x7000000000, 0x1000, -1);
    pages->Add(0x12000, 0x1000, -1);
    pages->Add(0x12000, 0x1000, 1);
    assert(pages->Any(0x12000, 1));
    // Beyond the table: taken as watched (the locked path).
    assert(pages->Any(0x10000000000ull, 8));
    std::puts("PASS: watched pages: per-page counts, ranges, overlap, untrack, outside the table");
}
