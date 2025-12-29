function renderStars(rating) {
  const filled = "★".repeat(rating);
  const empty = "☆".repeat(5 - rating);
  return filled + empty;
}

function calculateAverageRating(reviews) {
  if (!reviews || reviews.length === 0) {
    return 0; // レビューがない場合は0
  }

  const sum = reviews.reduce((total, review) => total + review.rating, 0);
  const average = sum / reviews.length;

  // 小数点第1位で四捨五入（例: 4.5 → 5, 4.3 → 4）
  return Math.round(average);
}

function createBookCard(book) {
  return `
    <div class="book-card">
      <h3>${book.title}</h3>
      <div>
        <img src="${book.imageUrl}" alt="${
    book.title
  }" width="100" height="100">
        <p>${book.reviews ? book.reviews.length : 0}人が読みました</p>
      </div>
    </div>
  `;
}

// データ取得と表示
fetch("../public/books.json")
  .then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then((data) => {
    const bookList = document.getElementById("book-list");

    if (!bookList) {
      throw new Error("Element with id 'book-list' not found");
    }

    // 各本のカードを作成して追加
    data.forEach((book) => {
      bookList.innerHTML += createBookCard(book);
    });
  })
  .catch((error) => {
    const bookList = document.getElementById("book-list");
    if (bookList) {
      bookList.innerHTML = `<p>Error loading books.json: ${error}</p>`;
    }
  });
