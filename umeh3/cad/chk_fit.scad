// fit check (review 2026-10-08): intersection of two placed parts; an empty result = no clash
include <umeh3.scad>
A = "shell"; B = "driver";
intersection() { placed(A); placed(B); }
