import streamlit as st
import urllib.parse
import requests
from supabase import create_client, Client

st.set_page_config(page_title="My Library", page_icon="📚", layout="wide")

supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

CATEGORIES = [
    "Novel", "Fantasy", "Science Fiction", "History",
    "Psychology", "Education", "Biography", "Poetry", "Other"
]

STATUSES = ["To Read", "Reading", "Completed"]


def create_book_link(title, author):
    query = urllib.parse.quote_plus(f"{title} {author}")
    return f"https://www.google.com/search?q={query}"

def restore_session():
    if "access_token" in st.session_state and "refresh_token" in st.session_state:
        try:
            supabase.auth.set_session(
                st.session_state["access_token"],
                st.session_state["refresh_token"]
            )
        except Exception:
            st.session_state.pop("access_token", None)
            st.session_state.pop("refresh_token", None)


def get_current_user():
    try:
        response = supabase.auth.get_user()
        return response.user
    except Exception:
        return None


def get_books(user_id):
    response = (
        supabase.table("books")
        .select("*")
        .eq("user_id", user_id)
        .order("id", desc=True)
        .execute()
    )
    return response.data if response.data else []


def add_book(user_id, book_data):
    book_data["user_id"] = user_id
    supabase.table("books").insert(book_data).execute()


def update_book(user_id, book_id, book_data):
    (
        supabase.table("books")
        .update(book_data)
        .eq("id", book_id)
        .eq("user_id", user_id)
        .execute()
    )


def delete_book(user_id, book_id):
    (
        supabase.table("books")
        .delete()
        .eq("id", book_id)
        .eq("user_id", user_id)
        .execute()
    )


def search_books_openlibrary(query):
    def search_wikipedia_book(title):
        try:
            search_url = "https://tr.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": title,
                "format": "json"
            }

            response = requests.get(search_url, params=search_params)
            data = response.json()

            results = data.get("query", {}).get("search", [])
            if not results:
                return None

            page_title = results[0]["title"]

            page_url = "https://tr.wikipedia.org/w/api.php"
            page_params = {
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "titles": page_title,
                "format": "json"
            }

            response = requests.get(page_url, params=page_params)
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            page = next(iter(pages.values()))

            extract = page.get("extract", "")

            return {
                "title": page_title,
                "summary": extract,
                "info_link": f"https://tr.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
            }

        except Exception:
            return None
    if not query.strip():
        return [], "Please enter a book title."

    url = "https://openlibrary.org/search.json"

    try:
        response = requests.get(url, params={"q": query}, timeout=10)
        response.raise_for_status()
        data = response.json()

        docs = data.get("docs", [])
        if not docs:
            return [], "No results found."

        return docs[:10], None

    except Exception as e:
        return [], f"Search failed: {e}"

        return items, None

    except requests.exceptions.RequestException as e:
        return [], f"Search failed: {e}"
    except Exception as e:
        return [], f"Unexpected error: {e}"


def extract_book_data(item):
    author = ", ".join(item.get("author_name", [])) if item.get("author_name") else ""

    cover_id = item.get("cover_i")
    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""

    return {
        "title": item.get("title", "") or "",
        "author": author,
        "publisher": ", ".join(item.get("publisher", [])) if item.get("publisher") else "",
        "page_count": item.get("number_of_pages_median", 1) or 1,
        "published_date": str(item.get("first_publish_year", "")),
        "cover_url": cover_url,
        "info_link": f"https://openlibrary.org{item.get('key')}" if item.get("key") else "",
    }


restore_session()

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "search_error" not in st.session_state:
    st.session_state.search_error = None

if "selected_book_data" not in st.session_state:
    st.session_state.selected_book_data = {
        "title": "",
        "author": "",
        "publisher": "",
        "page_count": 1,
        "published_date": "",
        "cover_url": "",
        "info_link": "",
    }

user = get_current_user()

st.title("📚 My Library")

if not user:
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

with tab1:
    st.subheader("Log In")
    login_email = st.text_input("Email", key="login_email")
    login_password = st.text_input("Password", type="password", key="login_password")
    remember_me = st.checkbox("Remember Me")

    if st.button("Log In"):
        try:
            response = supabase.auth.sign_in_with_password({
                "email": login_email,
                "password": login_password
            })

            st.session_state["access_token"] = response.session.access_token
            st.session_state["refresh_token"] = response.session.refresh_token

            if remember_me:
                st.session_state["remember_me"] = True

            st.success("Logged in successfully.")
            st.rerun()

        except Exception as e:
            st.error(f"Login failed: {e}")

with tab2:
    st.subheader("Sign Up")
    signup_email = st.text_input("Email", key="signup_email")
    signup_password = st.text_input("Password", type="password", key="signup_password")

    if st.button("Create Account"):
        try:
            supabase.auth.sign_up({
                "email": signup_email,
                "password": signup_password
            })
            st.success("Account created. You can now log in.")
        except Exception as e:
            st.error(f"Sign up failed: {e}")

st.stop()

st.success(f"Logged in as: {user.email}")

if st.button("Log Out"):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.pop("access_token", None)
    st.session_state.pop("refresh_token", None)
    st.session_state.pop("remember_me", None)
    st.session_state.edit_id = None
    st.rerun()

books = get_books(user.id)

st.subheader("Add a New Book")

entry_mode = st.radio(
    "Choose input method",
    ["Manual Entry", "Auto Fill from Web"],
    horizontal=True
)

if entry_mode == "Auto Fill from Web":
    web_search_query = st.text_input(
        "Search by book title";
        if st.button("Search Book", key="web_search_button_unique"):
    results, error = search_books_openlibrary(web_search_query)

    if not results:
        wiki_data = search_wikipedia_book(web_search_query)

        if wiki_data:
            st.session_state.selected_book_data = {
                "title": wiki_data["title"],
                "author": "",
                "publisher": "",
                "page_count": 1,
                "published_date": "",
                "cover_url": "",
                "info_link": wiki_data["info_link"],
            }
            st.session_state.search_results = []
            st.session_state.search_error = None
            st.info("Book found via Wikipedia. Some fields may be incomplete.")
        else:
            st.session_state.search_results = []
            st.session_state.search_error = "No results found anywhere."
    else:
        st.session_state.search_results = results
        st.session_state.search_error = error
        key="web_search_query_unique"
    )

    if st.button("Search Book", key="web_search_button_unique"):
        results, error = search_books_openlibrary(web_search_query)

        # Eğer Open Library boş dönerse → Wikipedia kullan
        if not results:
            wiki_data = search_wikipedia_book(web_search_query)

            if wiki_data:
                st.session_state.selected_book_data = {
                    "title": wiki_data["title"],
                    "author": "",
                    "publisher": "",
                    "page_count": 1,
                    "published_date": "",
                    "cover_url": "",
                    "info_link": wiki_data["info_link"],
                }
                st.session_state.search_results = []
                st.session_state.search_error = None

                st.info("Book found via Wikipedia. Some fields may be incomplete.")
            else:
                st.session_state.search_results = []
                st.session_state.search_error = "No results found anywhere."
       else:
    st.session_state.search_results = results
    st.session_state.search_error = error
    if st.session_state.search_error:
        st.warning(st.session_state.search_error)

    if st.session_state.search_results:
        def format_result(item):
            title = item.get("title", "Unknown title")
            authors = ", ".join(item.get("author_name", [])) if item.get("author_name") else "Unknown author"
            publisher = ", ".join(item.get("publisher", [])) if item.get("publisher") else "Unknown publisher"
            return f"{title} — {authors} — {publisher}"

        selected_item = st.selectbox(
            "Select a book",
            options=st.session_state.search_results,
            format_func=format_result,
            key="web_search_result_unique"
        )

        st.session_state.selected_book_data = extract_book_data(selected_item)
        selected_data = st.session_state.selected_book_data

        col1, col2 = st.columns([1, 3])

        with col1:
            if selected_data["cover_url"]:
                st.image(selected_data["cover_url"], width=140)

        with col2:
            st.write(f"**Title:** {selected_data['title']}")
            st.write(f"**Author:** {selected_data['author']}")
            st.write(f"**Publisher:** {selected_data['publisher']}")
            st.write(f"**Published Date:** {selected_data['published_date']}")
            st.write(f"**Page Count:** {selected_data['page_count']}")

            if selected_data["info_link"]:
                st.markdown(f"[Open book page]({selected_data['info_link']})")
default_data = st.session_state.selected_book_data if entry_mode == "Auto Fill from Web" else {
    "title": "",
    "author": "",
    "publisher": "",
    "page_count": 1,
    "published_date": "",
    "cover_url": "",
    "info_link": "",
}

with st.form("add_book_form", clear_on_submit=(entry_mode == "Manual Entry")):
    title = st.text_input("Title", value=default_data["title"])
    author = st.text_input("Author", value=default_data["author"])
    publisher = st.text_input("Publisher", value=default_data["publisher"])
    page_count = st.number_input(
        "Page Count",
        min_value=1,
        step=1,
        value=int(default_data["page_count"]) if default_data["page_count"] else 1
    )
    published_date = st.text_input("Published Date", value=default_data["published_date"])
    category = st.selectbox("Category", CATEGORIES)
    status = st.selectbox("Status", STATUSES)
    rating = st.slider("Rating", min_value=1, max_value=5, value=3)
    review = st.text_area("Review")

    submitted = st.form_submit_button("Add Book")

    if submitted:
        if not title.strip() or not author.strip():
            st.warning("Please fill in the Title and Author fields.")
        else:
            add_book(user.id, {
                "title": title.strip(),
                "author": author.strip(),
                "publisher": publisher.strip(),
                "page_count": int(page_count),
                "published_date": published_date.strip(),
                "category": category,
                "status": status,
                "rating": rating,
                "review": review.strip(),
                "cover_url": default_data["cover_url"] if entry_mode == "Auto Fill from Web" else "",
                "info_link": default_data["info_link"] if entry_mode == "Auto Fill from Web" else "",
            })
            st.session_state.selected_book_data = {
                "title": "",
                "author": "",
                "publisher": "",
                "page_count": 1,
                "published_date": "",
                "cover_url": "",
                "info_link": "",
            }
            st.session_state.search_results = []
            st.success(f'"{title}" has been added.')
            st.rerun()

st.markdown("---")
st.subheader("Search and Filter")

col1, col2, col3 = st.columns(3)

with col1:
    search_text = st.text_input("Search in my library")

with col2:
    category_filter = st.selectbox("Filter by Category", ["All"] + CATEGORIES)

with col3:
    status_filter = st.selectbox("Filter by Status", ["All"] + STATUSES)

filtered_books = []
for book in books:
    matches_search = (
        search_text.lower() in (book.get("title") or "").lower()
        or search_text.lower() in (book.get("author") or "").lower()
        or search_text.lower() in (book.get("publisher") or "").lower()
    ) if search_text else True

    matches_category = category_filter == "All" or book["category"] == category_filter
    matches_status = status_filter == "All" or book["status"] == status_filter

    if matches_search and matches_category and matches_status:
        filtered_books.append(book)

st.markdown("---")
st.subheader("My Books")

if not filtered_books:
    st.info("No books found.")
else:
    for book in filtered_books:
        col_left, col_right = st.columns([1, 4])

        with col_left:
            if book.get("cover_url"):
                st.image(book["cover_url"], width=120)

        with col_right:
            st.markdown(f"### {book['title']}")
            st.write(f"**Author:** {book['author']}")
            st.write(f"**Publisher:** {book.get('publisher', '') or 'Unknown'}")
            st.write(f"**Published Date:** {book.get('published_date', '') or 'Unknown'}")
            st.write(f"**Page Count:** {book['page_count']}")
            st.write(f"**Category:** {book['category']}")
            st.write(f"**Status:** {book['status']}")
            st.write(f"**Rating:** {'⭐' * book['rating']}")
            st.write(f"**Review:** {book['review'] if book['review'] else 'No review added.'}")

            if book.get("info_link"):
                st.markdown(f"[View book details]({book['info_link']})")
            else:
                st.markdown(f"[Search this book online]({create_book_link(book['title'], book['author'])})")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Edit", key=f"edit_{book['id']}"):
                    st.session_state.edit_id = book["id"]
                    st.rerun()
            with c2:
                if st.button("Delete", key=f"delete_{book['id']}"):
                    delete_book(user.id, book["id"])
                    if st.session_state.edit_id == book["id"]:
                        st.session_state.edit_id = None
                    st.rerun()

        st.markdown("---")

if st.session_state.edit_id is not None:
    current_book = next((b for b in books if b["id"] == st.session_state.edit_id), None)

    if current_book:
        st.subheader(f"Edit Book: {current_book['title']}")

        with st.form("edit_book_form"):
            new_title = st.text_input("Edit Title", value=current_book["title"])
            new_author = st.text_input("Edit Author", value=current_book["author"])
            new_publisher = st.text_input("Edit Publisher", value=current_book.get("publisher", "") or "")
            new_page_count = st.number_input(
                "Edit Page Count",
                min_value=1,
                step=1,
                value=int(current_book["page_count"])
            )
            new_published_date = st.text_input(
                "Edit Published Date",
                value=current_book.get("published_date", "") or ""
            )
            new_category = st.selectbox(
                "Edit Category",
                CATEGORIES,
                index=CATEGORIES.index(current_book["category"])
            )
            new_status = st.selectbox(
                "Edit Status",
                STATUSES,
                index=STATUSES.index(current_book["status"])
            )
            new_rating = st.slider(
                "Edit Rating",
                min_value=1,
                max_value=5,
                value=int(current_book["rating"])
            )
            new_review = st.text_area("Edit Review", value=current_book["review"] or "")

            save_button = st.form_submit_button("Save Changes")
            cancel_button = st.form_submit_button("Cancel")

            if save_button:
                update_book(user.id, current_book["id"], {
                    "title": new_title.strip(),
                    "author": new_author.strip(),
                    "publisher": new_publisher.strip(),
                    "page_count": int(new_page_count),
                    "published_date": new_published_date.strip(),
                    "category": new_category,
                    "status": new_status,
                    "rating": new_rating,
                    "review": new_review.strip()
                })
                st.session_state.edit_id = None
                st.success("Book updated successfully.")
                st.rerun()

            if cancel_button:
                st.session_state.edit_id = None
                st.rerun()
