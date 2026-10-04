# Address Tokenizer Assignment Specification

## Assignment Overview
Develop a **console program** capable of parsing and tokenizing a free-form text string into distinct address components.

---

## Technical Guidelines & Rules

### Input Constraints
- **Order-Agnostic:** User input can be provided in any component order.
- **Incomplete Addresses:** Each address component is completely optional.
- **Bonus Marks:** The parsing algorithm should successfully handle inputs **without commas**.

### Component Parsing Rules

| No | Address Component | Rule / Matching Criteria |
| :--- | :--- | :--- |
| **1** | **{Apt Number}** | Starts with `"No "` followed by a series of numbers. |
| **2** | **{City}** | Exact match with any of the following values:<br><ul><li>Kuala Terengganu</li><li>Kuala Lumpur</li><li>Kajang</li><li>Bangi</li><li>Damansara</li><li>Petaling Jaya</li><li>Puchong</li><li>Subang Jaya</li><li>Cyberjaya</li><li>Putrajaya</li><li>Mantin</li><li>Kuching</li><li>Seremban</li></ul> |
| **3** | **{State}** | Exact match with any of the following values:<br><ul><li>Selangor</li><li>Terengganu</li><li>Pahang</li><li>Kelantan</li><li>Melaka</li><li>Pulau Pinang</li><li>Kedah</li><li>Johor</li><li>Perlis</li><li>Sabah</li><li>Sarawak</li></ul> |
| **4** | **{Postcode}** | Numerical values within the inclusive range of `01000` to `98859`. |
| **5** | **{Street}** | Text fields beginning with:<br><ul><li>`"Jalan "`</li><li>`"Jln "`</li><li>`"Lorong "`</li><li>`"Persiaran"`</li></ul> |
| **6** | **{Section}** | Default catch-all rule: Any text block remaining unparsed by other rules. |

---

## Evaluation Criteria
- Architectural approach and design pattern choices.
- Proper implementation of **Object-Oriented Programming (OOP)** and **SOLID principles**.
- Robustness in handling input formatting anomalies and run-time errors gracefully.
- Parsing precision and output accuracy.

---

## Input / Output Examples

### Example 1: Full Address
**Input:**  
```text
No 11, Chendering, 21080 Kuala Terengganu, Terengganu.
```
**Output:**  
```json
{
  "apt": "No 11",
  "section": "Chendering",
  "postcode": "21080",
  "city": "Kuala Terengganu",
  "state": "Terengganu"
}
```

### Example 2: Incomplete Address
**Input:**  
```text
No 11, Kuala Terengganu, Chendering
```
**Output:**  
```json
{
  "apt": "No 11",
  "section": "Chendering",
  "city": "Kuala Terengganu"
}
```
