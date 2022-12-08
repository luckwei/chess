function range(start, end, interval = 1) {
    if (end === undefined) {
        end = start;
        start = 0;
    }

    let arr = [];
    for (let i = start; i < end; i += interval) {
        arr.push(i);
    }
    return arr;
}

function createPawn(element) {
    element.style.backgroundImage = 'url("../../res/pawn_white.svg")'
}

function createBoard(element) {
    
    for (row in range(8)) {
        for (col in range(8)) {
            tile = document.createElement("div");
            tile.classList.add("tile", row % 2 ? "odd-row" : "even-row");
            element.append(tile);
        }
    }
}

const cb = document.getElementById("chessboard");
createBoard(cb);
