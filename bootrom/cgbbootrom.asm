SECTION "bootrom", ROM0[$0000]
main:
.loop:
    
    ; Init stackpointer
    ld SP, $FFFE

    ; Enable LCD and background tilemap
    ld A, $91
    ld [$FF00+$40], A

    ; TODO: Restore register values?

    ; Determine if CGB or DMG ROM
    ld A, [$0143]
    bit 7, A            ; if 7 bit set = CGB, if not, zero flag is set
    call z, .DMG        ; conditional on zero flag
    ld A, $11           ; CGB
    jp end

.DMG
    ld A, $1

SECTION "epilog", ROM0[$00FE]
end:
    ld [$FF00+$50], A