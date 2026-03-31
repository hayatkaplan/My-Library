import streamlit as st
import json
import os
import urllib.parse

st.set_page_config(page_title="My Library", page_icon="📚", layout="wide")

FILE_NAME = "books.json"


def load_books():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
    return []


def save_books(books):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(books, file, ensure_ascii=False, indent=4)


def create_book_link(title, author):
    query = urllib.parse.quote_plus(f"{title} {author}")
    return f"https://www.google.com/search?q={query}"


if "books" not in st.session_state:
    st.session_state.books = load_books()

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None


st.title("📚 My Library")

st.markdown("Manage your personal book collection easily.")

# FORM SECTION
st.subheader("Add a New Book")

with st.form("add_book_form", clear_on_submit=True):
    title = st.text_input("Title")
    author = st.text_input("Author")
    page_count = st.number_input("Page Count", min_value=1, step=1)
    category = st.selectbox(
        "Category",
        ["Novel", "Fantasy", "Science Fiction", "History", "Psychology", "Education", "Biography", "Poetry", "Other"]
    )
    status = st.selectbox(
        "Status",
        ["To Read", "Reading", "Completed"]
    )
    rating = st.slider("Rating", min_value=1, max_value=5, value=3)
    review = st.text_area("Review")

    submitted = st.form_submit_button("Add Book")

    if submitted:
        if title.strip() == "" or author.strip() == "":
            st.warning("Please fill in the Title and Author fields.")
        else:
            book = {
                "title": title.strip(),
                "author": author.strip(),
                "page_count": int(page_count),
                "category": category,
                "status": status,
                "rating": rating,
                "review": review.strip()
            }
            st.session_state.books.append(book)
            save_books(st.session_state.books)
            st.success(f'"{title}" has been added to your library.')
            st.rerun()

st.markdown("---")

# SEARCH + FILTER SECTION
st.subheader("Search and Filter")

col1, col2, col3 = st.columns(3)

with col1:
    search_text = st.text_input("Search by title or author")

with col2:
    category_filter = st.selectbox(
        "Filter by Category",
        ["All"] + ["Novel", "Fantasy", "Science Fiction", "History", "Psychology", "Education", "Biography", "Poetry", "Other"]
    )

with col3:
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "To Read", "Reading", "Completed"]
    )

filtered_books = []

for i, book in enumerate(st.session_state.books):
    matches_search = (
        search_text.lower() in book["title"].lower()
        or search_text.lower() in book["author"].lower()
    ) if search_text else True

    matches_category = category_filter == "All" or book["category"] == category_filter
    matches_status = status_filter == "All" or book["status"] == status_filter

    if matches_search and matches_category and matches_status:
        filtered_books.append((i, book))

st.markdown("---")

# BOOK LIST SECTION
st.subheader("My Books")

if not filtered_books:
    st.info("No books found.")
else:
    for i, book in filtered_books:
        with st.container():
            st.markdown(
                f"""
                <div style="
                    border:1px solid #ddd;
                    border-radius:12px;
                    padding:18px;
                    margin-bottom:14px;
                    background-color:#f9f9f9;
                ">
                """,
                unsafe_allow_html=True
            )

            st.markdown(f"### {book['title']}")
            st.write(f"**Author:** {book['author']}")
            st.write(f"**Page Count:** {book['page_count']}")
            st.write(f"**Category:** {book['category']}")
            st.write(f"**Status:** {book['status']}")
            st.write(f"**Rating:** {'⭐' * book['rating']}")
            st.write(f"**Review:** {book['review'] if book['review'] else 'No review added.'}")

            link = create_book_link(book["title"], book["author"])
            st.markdown(f"[View this book online]({link})")

            button_col1, button_col2 = st.columns(2)

            with button_col1:
                if st.button("Edit", key=f"edit_{i}"):
                    st.session_state.edit_index = i
                    st.rerun()

            with button_col2:
                if st.button("Delete", key=f"delete_{i}"):
                    st.session_state.books.pop(i)
                    save_books(st.session_state.books)
                    if st.session_state.edit_index == i:
                        st.session_state.edit_index = None
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

# EDIT SECTION
if st.session_state.edit_index is not None:
    edit_index = st.session_state.edit_index
    book = st.session_state.books[edit_index]

    st.markdown("---")
    st.subheader(f"Edit Book: {book['title']}")

    with st.form("edit_book_form"):
        new_title = st.text_input("Edit Title", value=book["title"])
        new_author = st.text_input("Edit Author", value=book["author"])
        new_page_count = st.number_input("Edit Page Count", min_value=1, step=1, value=int(book["page_count"]))
        new_category = st.selectbox(
            "Edit Category",
            ["Novel", "Fantasy", "Science Fiction", "History", "Psychology", "Education", "Biography", "Poetry", "Other"],
            index=["Novel", "Fantasy", "Science Fiction", "History", "Psychology", "Education", "Biography", "Poetry", "Other"].index(book["category"])
        )
        new_status = st.selectbox(
            "Edit Status",
            ["To Read", "Reading", "Completed"],
            index=["To Read", "Reading", "Completed"].index(book["status"])
        )
        new_rating = st.slider("Edit Rating", min_value=1, max_value=5, value=int(book["rating"]))
        new_review = st.text_area("Edit Review", value=book["review"])

        save_button = st.form_submit_button("Save Changes")
        cancel_button = st.form_submit_button("Cancel")

        if save_button:
            if new_title.strip() == "" or new_author.strip() == "":
                st.warning("Title and Author cannot be empty.")
            else:
                st.session_state.books[edit_index] = {
                    "title": new_title.strip(),
                    "author": new_author.strip(),
                    "page_count": int(new_page_count),
                    "category": new_category,
                    "status": new_status,
                    "rating": new_rating,
                    "review": new_review.strip()
                }
                save_books(st.session_state.books)
                st.session_state.edit_index = None
                st.success("Book updated successfully.")
                st.rerun()

        if cancel_button:
            st.session_state.edit_index = None
            st.rerun()