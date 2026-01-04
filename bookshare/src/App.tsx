import { useState, useEffect } from "react";
import BookList from "./components/BookList";
import { Book } from "./types/book";
import BookDetail from "./components/BookDetail";

function App() {
  const [books, setBooks] = useState<Book[]>([]);
  const [selectedBookId, setSelectedBookId] = useState<string | null>(null);

  const handleSelectBook = (id: string) => {
    setSelectedBookId(id);
  };

  useEffect(() => {
    fetch("/books.json")
      .then(response => response.json())
      .then(data => setBooks(data))
      .catch(error => console.error("Error fetching books:", error));
  }, []);


  const selectedBook = books.find(book => book.id === selectedBookId)

  return (
    <div>
      <h1>BookShare</h1>
      { selectedBookId === null ? (
        <BookList books={books} onSelectBook={handleSelectBook} />
      ) :
      selectedBook === undefined ? (
        <p>書籍データを取得できませんでした。</p>
      ) : (
        <BookDetail book={selectedBook} onBack={() => setSelectedBookId(null)} />
      )}
    </div>
  );
}

export default App;
