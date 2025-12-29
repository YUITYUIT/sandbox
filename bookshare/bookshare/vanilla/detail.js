function renderStars(rating) {
  const filled = "★".repeat(rating);
  const empty = "☆".repeat(5 - rating);
  return filled + empty;
}

const params = new URLSearchParams(window.location.search);
const getBookId = params.get("id");

fetch(`../public/books.json`)
  .then((response) => response.json())
  .then((data) => {
    const foundBook = data.find((book) => book.id === getBookId);
    if (!foundBook) {
      document.getElementById("book-detail").innerHTML = `
        <p>本が見つかりませんでした</p>
      `;
      return;
    }
    const reviewsHtml = foundBook.reviews
      .map((review) => {
        return `
        <div>
          <p>読んだ人：${review.reader}</p>
          <p>評価：${renderStars(review.rating)}</p>
          <p>コメント：${review.comment}</p>
        </div>
      `;
      })
      .join("");

    document.getElementById("book-detail").innerHTML = `
    <button onclick="window.location.href='./index.html'">← 一覧に戻る</button>
    <h2>${foundBook.title}</h2>
    <p>${foundBook.author}</p>
    <img src="${foundBook.imageUrl}" alt="${foundBook.title}">
    ${reviewsHtml}
  `;
  })
  .catch((error) => {
    document.getElementById("book-detail").innerHTML = `
      <p>読み込みに失敗しました</p>
    `;
  });
